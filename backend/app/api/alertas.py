import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import exigir_perfil
from app.core.alertas import gerar_alertas
from app.models.usuario import Usuario, PerfilUsuario
from app.models.documento import Documento
from app.models.alerta_documento import AlertaDocumento
from app.schemas.alerta_documento import AlertaDocumentoOut

router = APIRouter(prefix="/alertas", tags=["Alertas"])

ADMIN = PerfilUsuario.COOPERATIVA_ADMIN
AUDITOR = PerfilUsuario.AUDITOR_COMPLIANCE


def _consulta_vigentes(db: Session):
    """Alertas + documento, só de documentos vigentes. Quando sobe
    uma nova versão, os alertas da versão antiga somem da lista."""
    return (
        db.query(AlertaDocumento, Documento)
        .join(Documento, Documento.id == AlertaDocumento.documento_id)
        .filter(Documento.vigente.is_(True))
    )


def _para_out(alerta: AlertaDocumento, doc: Documento) -> AlertaDocumentoOut:
    return AlertaDocumentoOut(
        id=alerta.id,
        documento_id=alerta.documento_id,
        tipo_alerta=alerta.tipo_alerta,
        mensagem=alerta.mensagem,
        lido=alerta.lido,
        criado_em=alerta.criado_em,
        documento_tipo=doc.tipo,
        entidade_tipo=doc.entidade_tipo,
        entidade_id=doc.entidade_id,
        data_validade=doc.data_validade,
    )


@router.get("/", response_model=list[AlertaDocumentoOut])
def listar_alertas(
    apenas_nao_lidos: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    consulta = _consulta_vigentes(db)
    if apenas_nao_lidos:
        consulta = consulta.filter(AlertaDocumento.lido.is_(False))
    linhas = consulta.order_by(AlertaDocumento.criado_em.desc()).all()
    return [_para_out(a, d) for a, d in linhas]


@router.get("/contagem")
def contar_nao_lidos(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    total = (
        _consulta_vigentes(db)
        .filter(AlertaDocumento.lido.is_(False))
        .count()
    )
    return {"nao_lidos": total}


@router.patch("/{alerta_id}/lido", response_model=AlertaDocumentoOut)
def marcar_como_lido(
    alerta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    linha = (
        _consulta_vigentes(db)
        .filter(AlertaDocumento.id == alerta_id)
        .first()
    )
    if not linha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado",
        )
    alerta, doc = linha
    alerta.lido = True
    db.commit()
    db.refresh(alerta)
    return _para_out(alerta, doc)


@router.post("/marcar-todos-lidos")
def marcar_todos_como_lidos(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    ids = [
        a.id
        for a, _ in _consulta_vigentes(db)
        .filter(AlertaDocumento.lido.is_(False))
        .all()
    ]
    if ids:
        (
            db.query(AlertaDocumento)
            .filter(AlertaDocumento.id.in_(ids))
            .update({"lido": True}, synchronize_session=False)
        )
        db.commit()
    return {"marcados": len(ids)}


@router.post("/gerar")
def gerar_agora(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    """Dispara a verificação manualmente (a rotina diária faz o mesmo)."""
    return {"criados": gerar_alertas(db)}