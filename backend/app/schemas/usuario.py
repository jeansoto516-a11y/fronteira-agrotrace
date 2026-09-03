import uuid
from pydantic import BaseModel, EmailStr

from app.models.usuario import PerfilUsuario


class UsuarioBase(BaseModel):
    """Campos compartilhados entre criação e leitura de usuário."""
    nome: str
    email: EmailStr
    perfil: PerfilUsuario


class UsuarioCreate(UsuarioBase):
    """O que a API recebe ao CRIAR um usuário (inclui senha em texto puro)."""
    senha: str


class UsuarioOut(UsuarioBase):
    """O que a API DEVOLVE ao consultar um usuário (nunca inclui a senha/hash)."""
    id: uuid.UUID
    ativo: bool

    model_config = {"from_attributes": True}