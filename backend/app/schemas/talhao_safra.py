import uuid

from pydantic import BaseModel

from app.schemas.talhao import TalhaoOut
from app.schemas.safra import SafraOut
from app.schemas.cultura import CulturaOut


class TalhaoSafraCreate(BaseModel):
    """O que a API recebe para vincular um talhão a uma safra e cultura."""
    talhao_id: uuid.UUID
    safra_id: uuid.UUID
    cultura_id: uuid.UUID


class TalhaoSafraOut(BaseModel):
    """
    O que a API devolve: o vínculo com os dados completos de cada
    entidade relacionada (não só os IDs), facilitando o consumo no frontend.
    """
    id: uuid.UUID
    talhao: TalhaoOut
    safra: SafraOut
    cultura: CulturaOut

    model_config = {"from_attributes": True}