from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import engine
from app.api import auth

app = FastAPI(title="Fronteira AgroTrace API")
app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "online", "projeto": "Fronteira AgroTrace"}


@app.get("/health/db")
def check_db():
    """Testa se a conexão com o PostgreSQL está funcionando."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "conectado com sucesso"}
    except Exception as e:
        return {"database": "erro", "detalhe": str(e)}