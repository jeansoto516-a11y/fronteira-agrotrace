import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual
from app.core.cruzamento import cruzar_talhao, cruzar_todos
from app.models.usuario import Usuario
from app.models.talhao import Talhao
from app.schemas.cruzamento import CruzamentoTalhaoOut

router = APIRouter(prefix="/cruzamentos", tags=["Cruzamentos"])


@router.get("/talhoes", response_model=list[CruzamentoTalhaoOut])
def cruzar_todos_os_talhoes(
    apenas_com_restricao: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """
    Cruza todos os talhões com a base de áreas embargadas/desmatamento.
    Use apenas_com_restricao=true para listar só os que têm sobreposição.
    """
    resultado = cruzar_todos(db)
    if apenas_com_restricao:
        resultado = [r for r in resultado if r["possui_restricao"]]
    return resultado


@router.get("/talhoes/{talhao_id}", response_model=CruzamentoTalhaoOut)
def cruzar_um_talhao(
    talhao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Cruza um talhão específico com a base de áreas restritas."""
    talhao = db.query(Talhao).filter(Talhao.id == talhao_id).first()
    if not talhao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talhão não encontrado",
        )
    return cruzar_talhao(db, talhao)