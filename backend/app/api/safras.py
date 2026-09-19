from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.safra import Safra
from app.schemas.safra import SafraCreate, SafraOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/safras", tags=["Safras"])


@router.post("/", response_model=SafraOut, status_code=status.HTTP_201_CREATED)
def criar_safra(
    dados: SafraCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Cadastra uma nova safra (ciclo de produção). Restrito a Cooperativa/Admin."""
    existente = db.query(Safra).filter(Safra.identificacao == dados.identificacao).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Safra já cadastrada")

    nova_safra = Safra(**dados.model_dump())
    db.add(nova_safra)
    db.commit()
    db.refresh(nova_safra)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Safra", usuario_id=usuario_atual.id,
        entidade_id=nova_safra.id, detalhes=f"Safra {nova_safra.identificacao} cadastrada",
    )

    return nova_safra


@router.get("/", response_model=list[SafraOut])
def listar_safras(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Lista todas as safras cadastradas."""
    return db.query(Safra).all()