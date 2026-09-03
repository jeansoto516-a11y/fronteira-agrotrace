from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import decodificar_token

# Diz ao Swagger onde fica a rota de login, para gerar o botão "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Lê o token JWT do cabeçalho Authorization, valida e retorna
    o usuário correspondente do banco. Usada em toda rota protegida.
    """
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None or payload.get("type") != "access":
        raise credenciais_invalidas

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise credenciais_invalidas

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None or not usuario.ativo:
        raise credenciais_invalidas

    return usuario


def exigir_perfil(*perfis_permitidos: PerfilUsuario):
    """
    Fábrica de dependência: use assim numa rota para restringir o acesso
    a determinados perfis. Exemplo:

        @router.get("/relatorio")
        def relatorio(usuario = Depends(exigir_perfil(PerfilUsuario.AUDITOR_COMPLIANCE))):
            ...
    """
    def verificador(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este recurso",
            )
        return usuario
    return verificador