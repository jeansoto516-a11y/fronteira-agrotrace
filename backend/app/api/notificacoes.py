import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import exigir_perfil
from app.core.notificacoes import gerar_notificacoes
from app.db.database import get_db
from app.models.notificacao import Notificacao, TipoNotificacao
from app.models.usuario import PerfilUsuario, Usuario
from app.schemas.notificacao import NotificacaoOut, ResumoNotificacoesOut

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])

ADMIN = PerfilUsuario.COOPERATIVA_ADMIN
AUDITOR = PerfilUsuario.AUDITOR_COMPLIANCE


@router.get("/", response_model=list[NotificacaoOut])
def listar_notificacoes(
    apenas_nao_lidos: bool = False,
    limite: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    """Notificações internas, as mais recentes primeiro."""
    consulta = db.query(Notificacao)
    if apenas_nao_lidos:
        consulta = consulta.filter(Notificacao.lido.is_(False))
    return consulta.order_by(Notificacao.criado_em.desc()).limit(limite).all()


@router.get("/resumo", response_model=ResumoNotificacoesOut)
def resumo_notificacoes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    """Contadores de não lidas, no total e por tipo (para o dashboard)."""
    linhas = (
        db.query(Notificacao.tipo, func.count(Notificacao.id))
        .filter(Notificacao.lido.is_(False))
        .group_by(Notificacao.tipo)
        .all()
    )
    contagem = {tipo: total for tipo, total in linhas}
    return ResumoNotificacoesOut(
        nao_lidos=sum(contagem.values()),
        documentos_vencendo=contagem.get(TipoNotificacao.DOCUMENTO_VENCENDO, 0),
        sobreposicoes_area=contagem.get(TipoNotificacao.SOBREPOSICAO_AREA, 0),
        etapas_pendentes=contagem.get(TipoNotificacao.ETAPA_PENDENTE, 0),
    )


@router.patch("/{notificacao_id}/lido", response_model=NotificacaoOut)
def marcar_como_lida(
    notificacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    notificacao = (
        db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
    )
    if notificacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada",
        )
    notificacao.lido = True
    db.commit()
    db.refresh(notificacao)
    return notificacao


@router.post("/marcar-todas-lidas")
def marcar_todas_como_lidas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN, AUDITOR)),
):
    marcadas = (
        db.query(Notificacao)
        .filter(Notificacao.lido.is_(False))
        .update({"lido": True}, synchronize_session=False)
    )
    db.commit()
    return {"marcadas": marcadas}


@router.post("/gerar")
def gerar_agora(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    """Dispara a geração manualmente (a rotina diária faz o mesmo)."""
    return gerar_notificacoes(db)