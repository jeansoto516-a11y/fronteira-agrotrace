from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.documento import Documento
from app.models.alerta_documento import AlertaDocumento, TipoAlerta

ROTULOS_TIPO = {
    "car": "CAR",
    "licenca_ambiental": "Licença ambiental",
    "laudo_tecnico": "Laudo técnico",
    "outro": "Documento",
}


def _classificar(dias: int) -> TipoAlerta | None:
    """Decide qual faixa de alerta vale para o documento hoje."""
    if dias < 0:
        return TipoAlerta.VENCIDO
    if dias <= 7:
        return TipoAlerta.VENCE_7_DIAS
    if dias <= 15:
        return TipoAlerta.VENCE_15_DIAS
    if dias <= 30:
        return TipoAlerta.VENCE_30_DIAS
    return None


def _montar_mensagem(doc: Documento, dias: int) -> str:
    rotulo = ROTULOS_TIPO.get(doc.tipo.value, "Documento")
    data_fmt = doc.data_validade.strftime("%d/%m/%Y")
    if dias < 0:
        situacao = f"vencido há {abs(dias)} dia(s) (venceu em {data_fmt})"
    elif dias == 0:
        situacao = f"vence hoje ({data_fmt})"
    else:
        situacao = f"vence em {dias} dia(s) ({data_fmt})"
    return f"{rotulo} v{doc.versao} ({doc.entidade_tipo.value}): {situacao}"[:300]


def gerar_alertas(db: Session, hoje: date | None = None) -> int:
    """
    Varre os documentos vigentes com data de validade e cria os
    alertas que ainda não existem. Retorna quantos alertas novos
    foram criados. Pode rodar quantas vezes quiser: não duplica.
    """
    hoje = hoje or date.today()
    limite = hoje + timedelta(days=30)

    documentos = (
        db.query(Documento)
        .filter(Documento.vigente.is_(True))
        .filter(Documento.data_validade.isnot(None))
        .filter(Documento.data_validade <= limite)
        .all()
    )
    if not documentos:
        return 0

    ids = [d.id for d in documentos]
    existentes = {
        (a.documento_id, a.tipo_alerta)
        for a in db.query(AlertaDocumento)
        .filter(AlertaDocumento.documento_id.in_(ids))
        .all()
    }

    criados = 0
    for doc in documentos:
        dias = (doc.data_validade - hoje).days
        tipo = _classificar(dias)
        if tipo is None or (doc.id, tipo) in existentes:
            continue
        db.add(
            AlertaDocumento(
                documento_id=doc.id,
                tipo_alerta=tipo,
                mensagem=_montar_mensagem(doc, dias),
            )
        )
        criados += 1

    if criados:
        db.commit()
    return criados