from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.core.security import (
    verificar_senha,
    criar_access_token,
    criar_refresh_token,
    decodificar_token,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica o usuário pelo email e senha.
    Retorna access_token (curta duração) e refresh_token (7 dias).
    """
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    # Mensagem genérica de propósito: não revelar se foi o email ou a
    # senha que estava errada, para não facilitar ataques de enumeração.
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha incorretos",
    )

    if not usuario:
        raise credenciais_invalidas

    if not verificar_senha(dados.senha, usuario.senha_hash):
        raise credenciais_invalidas

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado. Contate o administrador.",
        )

    dados_token = {"sub": str(usuario.id), "perfil": usuario.perfil.value}

    return TokenResponse(
        access_token=criar_access_token(dados_token),
        refresh_token=criar_refresh_token(dados_token),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(dados: RefreshRequest, db: Session = Depends(get_db)):
    """
    Recebe um refresh_token válido e devolve um novo par de tokens,
    sem precisar que o usuário faça login de novo.
    """
    payload = decodificar_token(dados.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )

    usuario_id = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou desativado",
        )

    dados_token = {"sub": str(usuario.id), "perfil": usuario.perfil.value}

    return TokenResponse(
        access_token=criar_access_token(dados_token),
        refresh_token=criar_refresh_token(dados_token),
    )