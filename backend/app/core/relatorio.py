import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.core.cadeia import montar_linha_do_tempo
from app.core.conformidade import avaliar_lote, DIAS_AVISO_VENCIMENTO
from app.models.area_restrita import AreaRestrita
from app.models.documento import Documento, EntidadeDocumento
from app.models.lote import Lote
from app.models.movimentacao_etapa import MovimentacaoEtapa
from app.models.sinalizacao_talhao import SinalizacaoTalhao
from app.models.usuario import Usuario

FUSO = ZoneInfo("America/Sao_Paulo")


def _coletar_origens(lote: Lote):
    """
    Colheitas do lote com a cadeia até o produtor (mesmo caminho da
    rastreabilidade reversa): Colheita → Talhão → Fazenda → Produtor.
    """
    linhas = []
    talhoes: dict = {}
    fazendas: dict = {}
    for vinculo in lote.colheitas_vinculadas:
        colheita = vinculo.colheita
        talhao_safra = colheita.talhao_safra
        talhao = talhao_safra.talhao
        fazenda = talhao.fazenda
        produtor = fazenda.produtor
        talhoes[talhao.id] = talhao
        fazendas[fazenda.id] = fazenda
        linhas.append(
            {
                "colheita_id": colheita.id,
                "data_colheita": colheita.data_colheita,
                "quantidade_kg": vinculo.quantidade_kg,
                "safra": talhao_safra.safra.identificacao,
                "cultura": talhao_safra.cultura.nome,
                "talhao_id": talhao.id,
                "talhao_nome": talhao.nome_identificador,
                "talhao_area_ha": round(
                    (talhao.area_calculada_m2 or 0) / 10_000, 2
                ),
                "fazenda_id": fazenda.id,
                "fazenda_nome": fazenda.nome,
                "municipio": fazenda.municipio,
                "estado": fazenda.estado,
                "produtor_nome": produtor.nome,
                "produtor_documento": produtor.cpf_cnpj,
            }
        )
    linhas.sort(
        key=lambda o: (
            o["fazenda_nome"], o["talhao_nome"], str(o["data_colheita"])
        )
    )
    return linhas, talhoes, fazendas


def _resumir_talhoes(talhoes: dict, origens: list[dict]) -> list[dict]:
    """Talhões de origem com área, ponto central, contorno e kg no lote."""
    kg_por_talhao: dict = {}
    for o in origens:
        kg_por_talhao[o["talhao_id"]] = (
            kg_por_talhao.get(o["talhao_id"], 0.0) + o["quantidade_kg"]
        )
    resultado = []
    for talhao_id, talhao in talhoes.items():
        forma = to_shape(talhao.poligono)
        resultado.append(
            {
                "id": talhao_id,
                "nome": talhao.nome_identificador,
                "fazenda_nome": talhao.fazenda.nome,
                "area_ha": round((talhao.area_calculada_m2 or 0) / 10_000, 2),
                "latitude": round(forma.centroid.y, 6),
                "longitude": round(forma.centroid.x, 6),
                "coordenadas": [(x, y) for x, y in forma.exterior.coords],
                "quantidade_kg": kg_por_talhao.get(talhao_id, 0.0),
            }
        )
    resultado.sort(key=lambda t: (t["fazenda_nome"], t["nome"]))
    return resultado


def _resumir_fazendas(fazendas: dict, origens: list[dict]) -> list[dict]:
    kg_por_fazenda: dict = {}
    for o in origens:
        kg_por_fazenda[o["fazenda_id"]] = (
            kg_por_fazenda.get(o["fazenda_id"], 0.0) + o["quantidade_kg"]
        )
    resultado = []
    for fazenda_id, fazenda in fazendas.items():
        resultado.append(
            {
                "id": fazenda_id,
                "nome": fazenda.nome,
                "municipio": fazenda.municipio,
                "estado": fazenda.estado,
                "produtor_nome": fazenda.produtor.nome,
                "produtor_documento": fazenda.produtor.cpf_cnpj,
                "quantidade_kg": kg_por_fazenda.get(fazenda_id, 0.0),
            }
        )
    resultado.sort(key=lambda f: f["nome"])
    return resultado


def _coletar_documentos(
    db: Session, talhoes: dict, fazendas: dict, hoje: date
) -> list[dict]:
    """Documentos vigentes das fazendas e talhões de origem."""
    ids = list(talhoes) + list(fazendas)
    if not ids:
        return []
    documentos = (
        db.query(Documento)
        .filter(Documento.vigente.is_(True))
        .filter(Documento.entidade_id.in_(ids))
        .all()
    )
    resultado = []
    for d in documentos:
        if d.entidade_tipo == EntidadeDocumento.FAZENDA:
            entidade_nome = fazendas[d.entidade_id].nome
        else:
            entidade_nome = talhoes[d.entidade_id].nome_identificador

        if d.data_validade is None:
            situacao = "sem_validade"
        else:
            dias = (d.data_validade - hoje).days
            if dias < 0:
                situacao = "vencido"
            elif dias <= DIAS_AVISO_VENCIMENTO:
                situacao = "a_vencer"
            else:
                situacao = "valido"

        resultado.append(
            {
                "entidade_tipo": d.entidade_tipo.value,
                "entidade_nome": entidade_nome,
                "tipo": d.tipo.value,
                "versao": d.versao,
                "nome_arquivo": d.nome_arquivo_original,
                "data_validade": d.data_validade,
                "situacao": situacao,
            }
        )
    resultado.sort(
        key=lambda x: (x["entidade_tipo"], x["entidade_nome"], x["tipo"])
    )
    return resultado


def _coletar_sinalizacoes(db: Session, talhoes: dict) -> list[dict]:
    """Sinalizações ativas de áreas restritas nos talhões de origem."""
    if not talhoes:
        return []
    linhas = (
        db.query(SinalizacaoTalhao, AreaRestrita, Usuario.nome)
        .select_from(SinalizacaoTalhao)
        .join(
            AreaRestrita,
            AreaRestrita.id == SinalizacaoTalhao.area_restrita_id,
        )
        .outerjoin(Usuario, Usuario.id == SinalizacaoTalhao.revisado_por_id)
        .filter(SinalizacaoTalhao.talhao_id.in_(list(talhoes)))
        .filter(SinalizacaoTalhao.ativa.is_(True))
        .all()
    )
    resultado = []
    for s, area, revisor in linhas:
        geometria = to_shape(area.geometria)
        resultado.append(
            {
                "talhao_id": s.talhao_id,
                "talhao_nome": talhoes[s.talhao_id].nome_identificador,
                "area_tipo": area.tipo.value,
                "area_identificador": area.identificador,
                "area_fonte": area.fonte,
                "area_data_referencia": area.data_referencia,
                "sobreposicao_ha": s.area_sobreposta_hectares,
                "percentual_do_talhao": s.percentual_do_talhao,
                "status_revisao": s.status_revisao.value,
                "parecer": s.parecer,
                "revisado_por": revisor,
                "revisado_em": s.revisado_em,
                "detectada_em": s.detectada_em,
                "coordenadas": [
                    [(x, y) for x, y in poligono.exterior.coords]
                    for poligono in geometria.geoms
                ],
            }
        )
    resultado.sort(key=lambda x: (x["talhao_nome"], x["area_identificador"]))
    return resultado


def _anexar_movimentacoes(db: Session, cadeia: dict) -> None:
    """Acrescenta o histórico de movimentações em cada etapa registrada."""
    ids = [e["id"] for e in cadeia["etapas"] if e["id"] is not None]
    por_etapa: dict = {}
    if ids:
        linhas = (
            db.query(MovimentacaoEtapa, Usuario.nome)
            .outerjoin(
                Usuario, Usuario.id == MovimentacaoEtapa.registrado_por_id
            )
            .filter(MovimentacaoEtapa.etapa_id.in_(ids))
            .order_by(
                MovimentacaoEtapa.ocorrida_em, MovimentacaoEtapa.criado_em
            )
            .all()
        )
        for m, nome in linhas:
            por_etapa.setdefault(m.etapa_id, []).append(
                {
                    "tipo": m.tipo.value,
                    "ocorrida_em": m.ocorrida_em,
                    "quantidade_kg": m.quantidade_kg,
                    "responsavel": m.responsavel,
                    "documento_referencia": m.documento_referencia,
                    "observacao": m.observacao,
                    "registrado_por": nome,
                }
            )
    for etapa in cadeia["etapas"]:
        etapa["movimentacoes"] = por_etapa.get(etapa["id"], [])


def coletar_dados_relatorio(
    db: Session, lote_id: uuid.UUID, usuario: Usuario
) -> dict | None:
    """
    Reúne tudo o que o relatório de rastreabilidade do lote mostra.
    Devolve None se o lote não existir.
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if lote is None:
        return None

    hoje = date.today()
    origens, talhoes, fazendas = _coletar_origens(lote)

    cadeia = montar_linha_do_tempo(db, lote.id)
    _anexar_movimentacoes(db, cadeia)

    return {
        "lote": {
            "id": lote.id,
            "codigo": lote.codigo_lote,
            "peso_total_kg": lote.peso_total_kg,
            "criado_em": lote.criado_em,
        },
        "gerado_em": datetime.now(FUSO),
        "gerado_por": {
            "nome": usuario.nome,
            "perfil": usuario.perfil.value,
        },
        "conformidade": avaliar_lote(db, lote.id, hoje),
        "origens": origens,
        "fazendas": _resumir_fazendas(fazendas, origens),
        "talhoes": _resumir_talhoes(talhoes, origens),
        "documentos": _coletar_documentos(db, talhoes, fazendas, hoje),
        "sinalizacoes": _coletar_sinalizacoes(db, talhoes),
        "cadeia": cadeia,
    }