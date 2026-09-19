import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.cultura import Cultura
from app.schemas.cultura import CulturaCreate, CulturaOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/culturas", tags=["Culturas"])


@router.post("/", response_model=CulturaOut, status_code=status.HTTP_201_CREATED)
def criar_cultura(
    dados: CulturaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Cadastra um novo tipo de cultura (ex: Soja, Café). Restrito a Cooperativa/Admin."""
    existente = db.query(Cultura).filter(Cultura.nome == dados.nome).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cultura já cadastrada")

    nova_cultura = Cultura(nome=dados.nome)
    db.add(nova_cultura)
    db.commit()
    db.refresh(nova_cultura)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Cultura", usuario_id=usuario_atual.id,
        entidade_id=nova_cultura.id, detalhes=f"Cultura {nova_cultura.nome} cadastrada",
    )

    return nova_cultura


@router.get("/", response_model=list[CulturaOut])
def listar_culturas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Lista todas as culturas cadastradas."""
    return db.query(Cultura).all()
