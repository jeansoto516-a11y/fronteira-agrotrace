import uuid
from datetime import datetime
from typing import Optional
from app.schemas.talhao import GeoJSONPolygon

from pydantic import BaseModel, field_validator


class ColheitaVinculada(BaseModel):
    """Uma colheita a ser incluída no lote, com a quantidade específica dela."""
    colheita_id: uuid.UUID
    quantidade_kg: float

    @field_validator("quantidade_kg")
    @classmethod
    def validar_quantidade(cls, valor: float) -> float:
        if valor <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
        return valor


class LoteCreate(BaseModel):
    """O que a API recebe ao formar um novo lote."""
    codigo_lote: str
    colheitas: list[ColheitaVinculada]

    @field_validator("colheitas")
    @classmethod
    def validar_pelo_menos_uma_colheita(cls, valor: list) -> list:
        if len(valor) == 0:
            raise ValueError("Um lote precisa de pelo menos uma colheita vinculada")
        return valor


class LoteOut(BaseModel):
    """O que a API devolve ao consultar um lote (visão simples, sem rastreabilidade)."""
    id: uuid.UUID
    codigo_lote: str
    peso_total_kg: Optional[float] = None
    criado_em: datetime

    model_config = {"from_attributes": True}


# --- Schemas específicos da rastreabilidade reversa ---

class OrigemTalhao(BaseModel):
    talhao_id: uuid.UUID
    nome_identificador: str
    area_hectares: Optional[float] = None
    poligono: GeoJSONPolygon


class OrigemFazenda(BaseModel):
    fazenda_id: uuid.UUID
    nome: str
    municipio: str
    estado: str


class OrigemProdutor(BaseModel):
    produtor_id: uuid.UUID
    nome: str
    cpf_cnpj: str


class ColheitaRastreada(BaseModel):
    """Uma colheita de origem, com a cadeia completa até o produtor."""
    colheita_id: uuid.UUID
    data_colheita: datetime
    quantidade_kg_no_lote: float  # quanto dessa colheita foi para o lote consultado
    safra: str
    cultura: str
    talhao: OrigemTalhao
    fazenda: OrigemFazenda
    produtor: OrigemProdutor


class RastreabilidadeLote(BaseModel):
    """Resposta completa da consulta de rastreabilidade reversa de um lote."""
    lote_id: uuid.UUID
    codigo_lote: str
    peso_total_kg: Optional[float] = None
    origens: list[ColheitaRastreada]