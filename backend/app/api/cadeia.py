import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual
from app.core.cadeia import montar_linha_do_tempo
from app.models.usuario import Usuario
from app.schemas.cadeia import LinhaDoTempoLoteOut

# Mesmo prefixo do router de lotes: o FastAPI aceita vários routers
# com o mesmo prefixo, e assim o lotes.py não precisa ser alterado.
router = APIRouter(prefix="/lotes", tags=["Cadeia"])


@router.get("/{lote_id}/cadeia", response_model=LinhaDoTempoLoteOut)
def consultar_cadeia(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """
    Linha do tempo de um lote: origem (montada pela rastreabilidade)
    seguida das etapas registradas (armazém, transporte, porto e
    exportação), em ordem, e a lista de etapas ainda não registradas.
    """
    linha = montar_linha_do_tempo(db, lote_id)
    if linha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote não encontrado",
        )
    return linha