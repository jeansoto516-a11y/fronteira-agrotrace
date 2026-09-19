import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ColheitaBase(BaseModel):
    data_colheita: datetime
    quantidade_kg: float
    latitude: float
    longitude: float

    @field_validator("quantidade_kg")
    @classmethod
    def validar_quantidade(cls, valor: float) -> float:
        if valor <= 0:
            raise ValueError("A quantidade colhida deve ser maior que zero")
        return valor

    @field_validator("data_colheita")
    @classmethod
    def validar_data_nao_futura(cls, valor: datetime) -> datetime:
        agora = datetime.now(valor.tzinfo)
        if valor > agora:
            raise ValueError("A data da colheita não pode estar no futuro")
        return valor


class ColheitaCreate(ColheitaBase):
    """O que a API recebe ao registrar uma colheita."""
    talhao_safra_id: uuid.UUID


class ColheitaOut(ColheitaBase):
    """O que a API devolve ao consultar uma colheita."""
    id: uuid.UUID
    talhao_safra_id: uuid.UUID
    criado_em: datetime

    model_config = {"from_attributes": True}