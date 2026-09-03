from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centrais do projeto, carregadas a partir do arquivo .env.
    Qualquer variável de ambiente nova deve ser declarada aqui também.
    """

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instância única (singleton) usada em todo o projeto.
# Importe assim: from app.core.config import settings
settings = Settings()