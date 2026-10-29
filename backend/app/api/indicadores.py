from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_usuario_atual
from app.core.indicadores import calcular_indicadores
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.indicadores import IndicadoresOut

router = APIRouter(tags=["Indicadores"])


@router.get("/indicadores", response_model=IndicadoresOut)
def obter_indicadores(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """
    Indicadores consolidados para o dashboard: volume rastreado,
    percentual de lotes certificados e alertas de documentos.
    """
    return calcular_indicadores(db)