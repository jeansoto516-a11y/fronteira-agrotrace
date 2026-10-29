from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.cadeia import montar_linha_do_tempo
from app.models.alerta_documento import AlertaDocumento
from app.models.area_restrita import AreaRestrita
from app.models.documento import Documento
from app.models.lote import Lote
from app.models.notificacao import Notificacao, TipoNotificacao
from app.models.sinalizacao_talhao import SinalizacaoTalhao, StatusRevisao
from app.models.talhao import Talhao

# Lote criado há mais de N dias com etapas sem registro vira notificação.
DIAS_LOTE_PARADO = 7

ROTULO_ETAPA = {
    "fazenda": "Origem (fazenda)",
    "armazem": "Armazém",
    "transporte": "Transporte",
    "porto": "Porto",
    "exportacao": "Exportação",
}


def _candidatas_documentos(db: Session) -> list[dict]:
    """Um alerta de documento vigente vira uma notificação."""
    linhas = (
        db.query(AlertaDocumento)
        .join(Documento, Documento.id == AlertaDocumento.documento_id)
        .filter(Documento.vigente.is_(True))
        .all()
    )
    return [
        {
            "tipo": TipoNotificacao.DOCUMENTO_VENCENDO,
            "chave": f"documento_vencendo:{a.id}",
            "mensagem": a.mensagem,
            "link": "/documentos",
        }
        for a in linhas
    ]


def _candidatas_sobreposicoes(db: Session) -> list[dict]:
    """Sinalização ativa aguardando revisão do auditor vira notificação."""
    linhas = (
        db.query(SinalizacaoTalhao, AreaRestrita, Talhao)
        .select_from(SinalizacaoTalhao)
        .join(AreaRestrita, AreaRestrita.id == SinalizacaoTalhao.area_restrita_id)
        .join(Talhao, Talhao.id == SinalizacaoTalhao.talhao_id)
        .filter(SinalizacaoTalhao.ativa.is_(True))
        .filter(SinalizacaoTalhao.status_revisao == StatusRevisao.PENDENTE)
        .all()
    )
    return [
        {
            "tipo": TipoNotificacao.SOBREPOSICAO_AREA,
            "chave": f"sobreposicao_area:{s.id}",
            "mensagem": (
                f"{talhao.nome_identificador} sobrepõe {area.tipo.value} "
                f"{area.identificador} ({s.area_sobreposta_hectares:.2f} ha): "
                "aguardando revisão do auditor"
            ),
            "link": "/auditoria",
        }
        for s, area, talhao in linhas
    ]


def _candidatas_etapas_pendentes(db: Session) -> list[dict]:
    """Lote com mais de N dias e etapas da cadeia sem registro."""
    limite = datetime.now(timezone.utc) - timedelta(days=DIAS_LOTE_PARADO)
    candidatas = []
    for lote in db.query(Lote).filter(Lote.criado_em <= limite).all():
        cadeia = montar_linha_do_tempo(db, lote.id)
        pendentes = cadeia["etapas_pendentes"] if cadeia else []
        if not pendentes:
            continue
        nomes = ", ".join(
            ROTULO_ETAPA.get(getattr(p, "value", p), str(getattr(p, "value", p)))
            for p in pendentes
        )
        candidatas.append(
            {
                "tipo": TipoNotificacao.ETAPA_PENDENTE,
                "chave": f"etapa_pendente:{lote.id}",
                "mensagem": (
                    f"Lote {lote.codigo_lote} tem mais de {DIAS_LOTE_PARADO} "
                    f"dias e ainda não registrou: {nomes}"
                ),
                "link": "/cadeia",
            }
        )
    return candidatas


def gerar_notificacoes(db: Session) -> dict:
    """
    Varre o sistema e cria as notificações que ainda não existem.
    Pode rodar quantas vezes quiser: a chave única impede duplicatas.
    Deve rodar depois do gerar_alertas, porque usa os alertas de documentos.
    """
    candidatas = (
        _candidatas_documentos(db)
        + _candidatas_sobreposicoes(db)
        + _candidatas_etapas_pendentes(db)
    )
    if not candidatas:
        return {"criadas": 0}

    chaves = [c["chave"] for c in candidatas]
    existentes = {
        chave
        for (chave,) in db.query(Notificacao.chave)
        .filter(Notificacao.chave.in_(chaves))
        .all()
    }

    criadas = 0
    for c in candidatas:
        if c["chave"] in existentes:
            continue
        db.add(
            Notificacao(
                tipo=c["tipo"],
                chave=c["chave"],
                mensagem=c["mensagem"][:300],
                link=c["link"],
            )
        )
        criadas += 1

    if criadas:
        db.commit()
    return {"criadas": criadas}