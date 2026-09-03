from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Engine: gerencia o pool de conexões com o PostgreSQL
engine = create_engine(settings.DATABASE_URL)

# Fábrica de sessões: cada requisição vai abrir/fechar uma sessão própria
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: todas as models (Produtor, Fazenda, Talhão etc.) vão herdar dela
Base = declarative_base()


def get_db():
    """
    Dependência do FastAPI: abre uma sessão de banco, entrega para a rota,
    e garante que ela seja fechada no final da requisição (mesmo se der erro).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()