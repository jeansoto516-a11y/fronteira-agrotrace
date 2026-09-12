import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class GeoJSONPolygon(BaseModel):
    """
    Representa um polígono no formato GeoJSON padrão:
    {
      "type": "Polygon",
      "coordinates": [[[lon, lat], [lon, lat], ..., [lon, lat]]]
    }
    O primeiro e o último ponto devem ser iguais (polígono fechado).
    Suporta apenas polígonos simples (sem "buracos" internos).
    """
    type: str = "Polygon"
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def validar_anel_fechado(cls, valor):
        anel_externo = valor[0]
        if anel_externo[0] != anel_externo[-1]:
            raise ValueError("O polígono deve ser fechado: o primeiro e o último ponto devem ser iguais")
        if len(anel_externo) < 4:
            raise ValueError("Um polígono precisa de pelo menos 4 pontos (3 vértices + fechamento)")
        return valor


class TalhaoBase(BaseModel):
    nome_identificador: str
    area_hectares: Optional[float] = None


class TalhaoCreate(TalhaoBase):
    """O que a API recebe ao criar um talhão."""
    fazenda_id: uuid.UUID
    poligono: GeoJSONPolygon


class TalhaoUpdate(BaseModel):
    """Edição parcial — todos os campos opcionais."""
    nome_identificador: Optional[str] = None
    area_hectares: Optional[float] = None
    poligono: Optional[GeoJSONPolygon] = None


class TalhaoOut(TalhaoBase):
    """O que a API devolve — o polígono volta no formato GeoJSON."""
    id: uuid.UUID
    fazenda_id: uuid.UUID
    criado_em: datetime
    poligono: GeoJSONPolygon

    model_config = {"from_attributes": True}