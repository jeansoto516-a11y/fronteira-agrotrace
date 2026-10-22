from fastapi import FastAPI
from app.api import alertas
from app.api import areas_restritas
from app.api import cruzamentos
from app.api import sinalizacoes
from app.api import cadeia
from app.api import etapas
from app.api import movimentacoes
from app.api import conformidade
from contextlib import asynccontextmanager
from sqlalchemy import text

import app.models  # noqa: F401 — garante que todas as models sejam registradas

from app.db.database import engine
from app.core.agendador import iniciar_agendador, parar_agendador
from app.api import auth
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, produtores
from app.api import auth, produtores, fazendas
from app.api import auth, produtores, fazendas, talhoes
from app.api import auth, produtores, fazendas, talhoes, culturas, safras, talhao_safra
from app.api import auth, produtores, fazendas, talhoes, culturas, safras, talhao_safra, colheitas
from app.api import auth, produtores, fazendas, talhoes, culturas, safras, talhao_safra, colheitas, lotes
from app.api import auth, produtores, fazendas, talhoes, culturas, safras, talhao_safra, colheitas, lotes, documentos

@asynccontextmanager
async def lifespan(_app: FastAPI):
    iniciar_agendador()
    yield
    parar_agendador()


app = FastAPI(title="Fronteira AgroTrace API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(produtores.router)
app.include_router(fazendas.router)
app.include_router(talhoes.router)
app.include_router(culturas.router)
app.include_router(safras.router)
app.include_router(talhao_safra.router)
app.include_router(colheitas.router)
app.include_router(lotes.router)
app.include_router(documentos.router)   
app.include_router(alertas.router)
app.include_router(areas_restritas.router)
app.include_router(cruzamentos.router)
app.include_router(sinalizacoes.router)
app.include_router(cadeia.router)
app.include_router(etapas.router)
app.include_router(movimentacoes.router)
app.include_router(conformidade.router)

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