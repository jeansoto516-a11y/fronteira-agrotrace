from datetime import date

from sqlalchemy.orm import Session

from app.core.conformidade import StatusConformidade, avaliar_todos
from app.models.alerta_documento import AlertaDocumento, TipoAlerta
from app.models.documento import Documento

# Menor número = mais grave.
GRAVIDADE_ALERTA = {
    TipoAlerta.VENCIDO: 0,
    TipoAlerta.VENCE_7_DIAS: 1,
    TipoAlerta.VENCE_15_DIAS: 2,
    TipoAlerta.VENCE_30_DIAS: 3,
}


def _calcular_volume(avaliacoes: list[dict]) -> dict:
    """Soma do peso dos lotes (ignora vazios), total e por conformidade."""
    por_status = {status: 0.0 for status in StatusConformidade}
    for a in avaliacoes:
        por_status[a["status"]] += float(a["peso_total_kg"] or 0)
    return {
        "total_kg": sum(por_status.values()),
        "por_status": {
            "completo_kg": por_status[StatusConformidade.COMPLETO],
            "pendente_kg": por_status[StatusConformidade.PENDENTE],
            "vencido_kg": por_status[StatusConformidade.VENCIDO],
        },
    }


def _calcular_certificados(avaliacoes: list[dict]) -> dict:
    """Lotes completos / lotes que têm pelo menos uma origem."""
    com_origem = [a for a in avaliacoes if a["total_fazendas"] > 0]
    certificados = sum(
        1 for a in com_origem if a["status"] == StatusConformidade.COMPLETO
    )
    total = len(com_origem)
    percentual = round(certificados / total * 100, 1) if total else 0.0
    return {
        "total_lotes": total,
        "certificados": certificados,
        "percentual": percentual,
    }


def _calcular_alertas(db: Session) -> dict:
    """
    Conta documentos vigentes em alerta, usando só a faixa mais grave
    de cada documento (um documento pode ter várias linhas de alerta).
    """
    alertas = (
        db.query(AlertaDocumento)
        .join(Documento, Documento.id == AlertaDocumento.documento_id)
        .filter(Documento.vigente.is_(True))
        .all()
    )
    mais_grave: dict = {}
    for alerta in alertas:
        atual = mais_grave.get(alerta.documento_id)
        if (
            atual is None
            or GRAVIDADE_ALERTA[alerta.tipo_alerta]
            < GRAVIDADE_ALERTA[atual.tipo_alerta]
        ):
            mais_grave[alerta.documento_id] = alerta

    contagem = {tipo: 0 for tipo in TipoAlerta}
    nao_lidos = 0
    for alerta in mais_grave.values():
        contagem[alerta.tipo_alerta] += 1
        if not alerta.lido:
            nao_lidos += 1

    return {
        "documentos_em_alerta": len(mais_grave),
        "vencidos": contagem[TipoAlerta.VENCIDO],
        "vencem_7_dias": contagem[TipoAlerta.VENCE_7_DIAS],
        "vencem_15_dias": contagem[TipoAlerta.VENCE_15_DIAS],
        "vencem_30_dias": contagem[TipoAlerta.VENCE_30_DIAS],
        "nao_lidos": nao_lidos,
    }


def calcular_indicadores(db: Session, hoje: date | None = None) -> dict:
    """Indicadores consolidados: volume, % de lotes certificados e alertas."""
    hoje = hoje or date.today()
    avaliacoes = avaliar_todos(db, hoje)
    return {
        "gerado_em": hoje,
        "volume_rastreado": _calcular_volume(avaliacoes),
        "lotes_certificados": _calcular_certificados(avaliacoes),
        "alertas": _calcular_alertas(db),
    }