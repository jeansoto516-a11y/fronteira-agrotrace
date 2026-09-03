from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """O que a API recebe na rota de login."""
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    """O que a API devolve após um login bem-sucedido."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """O que a API recebe na rota de refresh token."""
    refresh_token: str