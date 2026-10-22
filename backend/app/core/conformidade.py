import enum
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.models.documento import Documento, TipoDocumento, EntidadeDocumento
from app.models.sinalizacao_talhao import SinalizacaoTalhao, StatusRevisao
from app.models.area_restrita import AreaRestrita

# ---------------------------------------------------------------------------
# Regras de negócio (ajuste aqui, se o cliente exigir outra lista)
# ---------------------------------------------------------------------------

# Documentos que cada tipo de entidade de origem precisa ter, vigentes.
DOCUMENTOS_OBRIGATORIOS = {
    EntidadeDocumento.FAZENDA: [
        TipoDocumento.CAR,
        TipoDocumento.LICENCA_AMBIENTAL,
    ],
    EntidadeDocumento.TALHAO: [
        TipoDocumento.LAUDO_TECNICO,
    ],
}

# Documento que vence em até N dias gera um aviso (não muda o status).
DIAS_AVISO_VENCIMENTO = 30

ROTULO_DOCUMENTO = {
    TipoDocumento.CAR: "CAR",
    TipoDocumento.LICENCA_AMBIENTAL: "Licença ambiental",
    TipoDocumento.LAUDO_TECNICO: "Laudo técnico",
    TipoDocumento.OUTRO: "Documento",
}


class StatusConformidade(str, enum.Enum):
    COMPLETO = "completo"
    PENDENTE = "pendente"
    VENCIDO = "vencido"


class TipoMotivo(str, enum.Enum):
    DOCUMENTO_AUSENTE = "documento_ausente"
    DOCUMENTO_VENCIDO = "documento_vencido"
    DOCUMENTO_A_VENCER = "documento_a_vencer"
    RESTRICAO_PENDENTE_REVISAO = "restricao_pendente_revisao"
    RESTRICAO_CONFIRMADA = "restricao_confirmada"


class Severidade(str, enum.Enum):
    IMPEDITIVO = "impeditivo"
    ATENCAO = "atencao"


def _motivo(
    tipo: TipoMotivo,
    severidade: Severidade,
    entidade_tipo: str,
    entidade_id: uuid.UUID,
    entidade_nome: str,
    detalhe: str,
    documento_tipo: str | None = None,
    data_validade: date | None = None,
) -> dict:
    return {
        "tipo": tipo,
        "severidade": severidade,
        "entidade_tipo": entidade_tipo,
        "entidade_id": entidade_id,
        "entidade_nome": entidade_nome,
        "documento_tipo": documento_tipo,
        "data_validade": data_validade,
        "detalhe": detalhe,
    }


def _escolher_documento(docs: list[Documento]) -> Documento:
    """
    Se houver mais de um documento vigente do mesmo tipo para a mesma
    entidade, vale o de validade mais longa (sem validade = sem prazo).
    """
    return max(docs, key=lambda d: d.data_validade or date.max)


def _checar_documentos(
    entidade_tipo: EntidadeDocumento,
    entidades: dict,
    nome_de,
    docs_por_chave: dict,
    hoje: date,
    motivos: list,
) -> None:
    for entidade_id, entidade in entidades.items():
        nome = nome_de(entidade)
        for tipo_doc in DOCUMENTOS_OBRIGATORIOS[entidade_tipo]:
            rotulo = ROTULO_DOCUMENTO[tipo_doc]
            docs = docs_por_chave.get((entidade_tipo, entidade_id, tipo_doc))

            if not docs:
                motivos.append(
                    _motivo(
                        TipoMotivo.DOCUMENTO_AUSENTE,
                        Severidade.IMPEDITIVO,
                        entidade_tipo.value, entidade_id, nome,
                        f"{rotulo} não cadastrado para {nome}",
                        documento_tipo=tipo_doc.value,
                    )
                )
                continue

            doc = _escolher_documento(docs)
            if doc.data_validade is None:
                continue  # sem validade informada: conta como válido

            dias = (doc.data_validade - hoje).days
            data_fmt = doc.data_validade.strftime("%d/%m/%Y")
            if dias < 0:
                motivos.append(
                    _motivo(
                        TipoMotivo.DOCUMENTO_VENCIDO,
                        Severidade.IMPEDITIVO,
                        entidade_tipo.value, entidade_id, nome,
                        f"{rotulo} de {nome} vencido há {abs(dias)} dia(s) "
                        f"(venceu em {data_fmt})",
                        documento_tipo=tipo_doc.value,
                        data_validade=doc.data_validade,
                    )
                )
            elif dias <= DIAS_AVISO_VENCIMENTO:
                quando = "vence hoje" if dias == 0 else f"vence em {dias} dia(s)"
                motivos.append(
                    _motivo(
                        TipoMotivo.DOCUMENTO_A_VENCER,
                        Severidade.ATENCAO,
                        entidade_tipo.value, entidade_id, nome,
                        f"{rotulo} de {nome} {quando} ({data_fmt})",
                        documento_tipo=tipo_doc.value,
                        data_validade=doc.data_validade,
                    )
                )


def avaliar_lote(
    db: Session, lote_id: uuid.UUID, hoje: date | None = None
) -> dict | None:
    """
    Status de conformidade de um lote (completo / pendente / vencido),
    com os motivos. Devolve None se o lote não existir.
    'hoje' existe só para simulações e testes.
    """
    hoje = hoje or date.today()
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if lote is None:
        return None

    # Origens do lote, pela rastreabilidade
    talhoes: dict = {}
    fazendas: dict = {}
    for vinculo in lote.colheitas_vinculadas:
        talhao = vinculo.colheita.talhao_safra.talhao
        talhoes[talhao.id] = talhao
        fazendas[talhao.fazenda.id] = talhao.fazenda

    motivos: list[dict] = []

    # Documentos vigentes das fazendas e talhões de origem
    ids = list(talhoes) + list(fazendas)
    documentos = []
    if ids:
        documentos = (
            db.query(Documento)
            .filter(Documento.vigente.is_(True))
            .filter(Documento.entidade_id.in_(ids))
            .all()
        )
    docs_por_chave: dict = {}
    for d in documentos:
        docs_por_chave.setdefault(
            (d.entidade_tipo, d.entidade_id, d.tipo), []
        ).append(d)

    _checar_documentos(
        EntidadeDocumento.FAZENDA, fazendas, lambda f: f.nome,
        docs_por_chave, hoje, motivos,
    )
    _checar_documentos(
        EntidadeDocumento.TALHAO, talhoes, lambda t: t.nome_identificador,
        docs_por_chave, hoje, motivos,
    )

    # Sinalizações ativas de áreas restritas nos talhões de origem
    if talhoes:
        linhas = (
            db.query(
                SinalizacaoTalhao,
                AreaRestrita.identificador,
                AreaRestrita.tipo,
            )
            .select_from(SinalizacaoTalhao)
            .join(
                AreaRestrita,
                AreaRestrita.id == SinalizacaoTalhao.area_restrita_id,
            )
            .filter(SinalizacaoTalhao.talhao_id.in_(list(talhoes)))
            .filter(SinalizacaoTalhao.ativa.is_(True))
            .all()
        )
        for sinalizacao, identificador, tipo_area in linhas:
            talhao = talhoes[sinalizacao.talhao_id]
            nome = talhao.nome_identificador
            base = (
                f"{nome} sobrepõe {tipo_area.value} {identificador} "
                f"({sinalizacao.area_sobreposta_hectares:.2f} ha)"
            )
            if sinalizacao.status_revisao == StatusRevisao.PENDENTE:
                motivos.append(
                    _motivo(
                        TipoMotivo.RESTRICAO_PENDENTE_REVISAO,
                        Severidade.IMPEDITIVO,
                        EntidadeDocumento.TALHAO.value, talhao.id, nome,
                        f"{base}: aguardando revisão do auditor",
                    )
                )
            elif sinalizacao.status_revisao == StatusRevisao.CONFIRMADA:
                motivos.append(
                    _motivo(
                        TipoMotivo.RESTRICAO_CONFIRMADA,
                        Severidade.IMPEDITIVO,
                        EntidadeDocumento.TALHAO.value, talhao.id, nome,
                        f"{base}: sobreposição confirmada pelo auditor",
                    )
                )
            # DESCARTADA: o auditor concluiu que não há restrição

    impeditivos = [m for m in motivos if m["severidade"] == Severidade.IMPEDITIVO]
    avisos = [m for m in motivos if m["severidade"] == Severidade.ATENCAO]

    if any(m["tipo"] == TipoMotivo.DOCUMENTO_VENCIDO for m in motivos):
        status = StatusConformidade.VENCIDO
    elif impeditivos:
        status = StatusConformidade.PENDENTE
    else:
        status = StatusConformidade.COMPLETO

    # Impeditivos primeiro, depois avisos
    motivos.sort(key=lambda m: (m["severidade"] != Severidade.IMPEDITIVO,))

    return {
        "lote_id": lote.id,
        "codigo_lote": lote.codigo_lote,
        "peso_total_kg": lote.peso_total_kg,
        "status": status,
        "avaliado_em": hoje,
        "total_fazendas": len(fazendas),
        "total_talhoes": len(talhoes),
        "total_impeditivos": len(impeditivos),
        "total_avisos": len(avisos),
        "motivos": motivos,
    }


def avaliar_todos(db: Session, hoje: date | None = None) -> list[dict]:
    """Avalia todos os lotes (um por vez: suficiente para o volume atual)."""
    lotes = db.query(Lote).order_by(Lote.codigo_lote).all()
    return [avaliar_lote(db, l.id, hoje) for l in lotes]