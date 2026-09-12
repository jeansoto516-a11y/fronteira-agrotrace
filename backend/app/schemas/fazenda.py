import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class FazendaBase(BaseModel):
    nome: str
    municipio: str
    estado: str
    area_total_hectares: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, valor: str) -> str:
        """Garante que o estado seja sempre salvo em maiúsculas (ex: 'mt' -> 'MT')."""
        if len(valor) != 2:
            raise ValueError("Estado deve ter exatamente 2 letras (ex: MT, BA)")
        return valor.upper()


class FazendaCreate(FazendaBase):
    """O que a API recebe ao criar uma fazenda. Exige o produtor dono dela."""
    produtor_id: uuid.UUID


class FazendaUpdate(BaseModel):
    """Edição parcial — todos os campos opcionais."""
    nome: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    area_total_hectares: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FazendaOut(FazendaBase):
    """O que a API devolve. Note que latitude/longitude aqui são
    extraídas do campo geoespacial 'localizacao' na hora da resposta
    (não são armazenadas diretamente como colunas simples)."""
    id: uuid.UUID
    produtor_id: uuid.UUID
    criado_em: datetime

    model_config = {"from_attributes": True}