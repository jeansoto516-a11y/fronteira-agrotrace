import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models.area_restrita import TipoAreaRestrita


class InterseccaoOut(BaseModel):
    area_id: uuid.UUID
    tipo: TipoAreaRestrita
    identificador: str
    descricao: Optional[str] = None
    fonte: str
    data_referencia: date
    area_sobreposta_hectares: float
    percentual_do_talhao: float


class CruzamentoTalhaoOut(BaseModel):
    talhao_id: uuid.UUID
    nome_identificador: str
    fazenda_id: uuid.UUID
    area_talhao_hectares: Optional[float] = None
    possui_restricao: bool
    interseccoes: list[InterseccaoOut]