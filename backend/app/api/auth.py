from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.usuario import UsuarioOut, UsuarioCreate
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.core.security import (
    verificar_senha,
    gerar_hash_senha,
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


@router.get("/me", response_model=UsuarioOut)
def meu_perfil(usuario_atual: Usuario = Depends(get_usuario_atual)):
    """Retorna os dados do usuário autenticado (qualquer perfil pode acessar)."""
    return usuario_atual


@router.get("/somente-admin")
def rota_restrita(usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN))):
    """Rota de teste: só usuários com perfil Cooperativa/Admin podem acessar."""
    return {"mensagem": f"Bem-vindo, {usuario_atual.nome}! Você é admin."}


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """
    Cadastra um novo usuário no sistema. Somente usuários com perfil
    Cooperativa/Admin podem criar novos usuários (de qualquer perfil).
    """
    email_existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if email_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com esse email",
        )

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=dados.perfil,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario