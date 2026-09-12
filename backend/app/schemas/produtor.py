import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class ProdutorBase(BaseModel):
    nome: str
    cpf_cnpj: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("cpf_cnpj")
    @classmethod
    def limpar_cpf_cnpj(cls, valor: str) -> str:
        """Remove pontos, traços e barras, guardando só os números."""
        return "".join(filter(str.isdigit, valor))


class ProdutorCreate(ProdutorBase):
    """O que a API recebe ao criar um produtor."""
    pass


class ProdutorUpdate(BaseModel):
    """
    O que a API recebe ao editar um produtor. Todos os campos são
    opcionais, já que uma edição pode alterar só parte dos dados.
    """
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None


class ProdutorOut(ProdutorBase):
    """O que a API devolve ao consultar um produtor."""
    id: uuid.UUID
    criado_em: datetime

    model_config = {"from_attributes": True}