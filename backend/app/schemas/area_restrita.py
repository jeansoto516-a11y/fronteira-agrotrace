import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.area_restrita import TipoAreaRestrita


class GeoJSONMultiPolygon(BaseModel):
    """
    Geometria no formato GeoJSON padrão:
    {
      "type": "MultiPolygon",
      "coordinates": [ [ [[lon, lat], ...] ], [ [[lon, lat], ...] ] ]
    }
    Cada item da lista externa é um polígono (uma "mancha" da área).
    """
    type: str = "MultiPolygon"
    coordinates: list[list[list[list[float]]]]


class AreaRestritaOut(BaseModel):
    """O que a API devolve: a geometria volta em GeoJSON."""
    id: uuid.UUID
    tipo: TipoAreaRestrita
    identificador: str
    descricao: Optional[str] = None
    fonte: str
    data_referencia: date
    criado_em: Optional[datetime] = None
    area_hectares: Optional[float] = None
    geometria: GeoJSONMultiPolygon

    model_config = {"from_attributes": True}