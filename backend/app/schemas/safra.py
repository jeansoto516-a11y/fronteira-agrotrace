import uuid

from pydantic import BaseModel, field_validator


class SafraBase(BaseModel):
    identificacao: str  # ex: "2025/2026"
    ano_inicio: int
    ano_fim: int

    @field_validator("ano_fim")
    @classmethod
    def validar_anos(cls, ano_fim: int, info) -> int:
        ano_inicio = info.data.get("ano_inicio")
        if ano_inicio and ano_fim < ano_inicio:
            raise ValueError("O ano final não pode ser anterior ao ano inicial")
        return ano_fim


class SafraCreate(SafraBase):
    pass


class SafraOut(SafraBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}