import uuid

from pydantic import BaseModel


class CulturaBase(BaseModel):
    nome: str


class CulturaCreate(CulturaBase):
    pass


class CulturaOut(CulturaBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}