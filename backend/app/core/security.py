from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError

from app.core.config import settings

# Contexto do passlib: define qual algoritmo de hash usar (bcrypt é o padrão
# recomendado hoje em dia — seguro e testado em produção há anos).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def gerar_hash_senha(senha: str) -> str:
    """
    Transforma a senha em texto puro (ex: 'minhasenha123') em um hash
    seguro para guardar no banco. NUNCA guardamos a senha original.
    """
    return pwd_context.hash(senha)


def verificar_senha(senha_texto: str, senha_hash: str) -> bool:
    """
    Compara a senha digitada no login com o hash guardado no banco.
    Retorna True se bater, False se não bater.
    """
    return pwd_context.verify(senha_texto, senha_hash)

def criar_access_token(dados: dict, expira_em: Optional[timedelta] = None) -> str:
    """
    Gera um token JWT de acesso (curta duração) contendo os dados
    informados (normalmente: id e perfil do usuário).
    """
    para_codificar = dados.copy()
    expira = datetime.now(timezone.utc) + (
        expira_em or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    para_codificar.update({"exp": expira, "type": "access"})
    return jwt.encode(para_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def criar_refresh_token(dados: dict) -> str:
    """
    Gera um token JWT de refresh (longa duração, 7 dias), usado para
    obter um novo access_token sem precisar fazer login de novo.
    """
    para_codificar = dados.copy()
    expira = datetime.now(timezone.utc) + timedelta(days=7)
    para_codificar.update({"exp": expira, "type": "refresh"})
    return jwt.encode(para_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    """
    Valida o token e retorna os dados dentro dele (payload).
    Retorna None se o token for inválido ou tiver expirado.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None