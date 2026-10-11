# Fronteira AgroTrace

Plataforma de rastreabilidade de commodities agrícolas (soja e café),
do talhão até a exportação, com geolocalização das áreas produtivas e
gestão de certificação socioambiental (exigências tipo EUDR).

**Cliente:** Sertões Agroexportadora (MT e BA)

## Stack

**Backend:** Python + FastAPI, SQLAlchemy, GeoAlchemy2, Alembic,
PostgreSQL + PostGIS, JWT (python-jose + passlib), WeasyPrint (PDF)

**Frontend:** Next.js + TypeScript, shadcn/ui, react-leaflet,
leaflet-draw, axios

Documentos enviados ficam em disco local (`backend/uploads/`).

## Estrutura

```
fronteira-agrotrace/
├── backend/    # API FastAPI (app/api, models, schemas, core, db)
├── frontend/   # Next.js (app/, components/, lib/, contexts/)
├── docs/
└── README.md
```

## Funcionalidades prontas

- Autenticação JWT + refresh token e 4 perfis (RBAC): produtor,
  cooperativa_admin, auditor_compliance, exportador
- CRUD de produtores, fazendas (ponto) e talhões (polígono GeoJSON)
- Área do talhão calculada via PostGIS (ST_Area)
- Culturas, safras e vínculo talhão → safra → cultura
- Registro de colheita com geolocalização e data
- Formação de lotes e rastreabilidade reversa até o produtor
- Mapa com os talhões de origem de cada lote
- Documentos de certificação (CAR, licenças, laudos) com upload,
  versionamento e controle de validade
- Auditoria de ações (log de atividades)

## Telas do frontend

Login, dashboard, produtores, fazendas, talhões (desenho de polígono
no mapa), safras/culturas, colheitas (ponto no mapa), lotes
(composição e rastreabilidade com mapa).

## Status (33 de 58 tarefas)

| Fase | Status |
|------|--------|
| 1 Setup e infraestrutura | Concluída |
| 2 Autenticação e perfis | Concluída |
| 3 Modelagem de dados core | Concluída |
| 4 Produtores, fazendas, talhões | Concluída |
| 5 Safras e culturas | Concluída |
| 6 Colheita e coleta | Concluída |
| 7 Lotes e rastreabilidade | Concluída |
| 8 Certificação socioambiental | Em andamento |
| 9 a 16 | Pendentes |

## Como rodar (Windows / PowerShell)

Pré-requisitos: Python 3.14, Node.js, PostgreSQL 18 com PostGIS.

**Banco:** criar o banco `agrotrace_db` e rodar
`CREATE EXTENSION postgis;` nele.

**Backend:**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Criar `backend\.env`:

```
DATABASE_URL=postgresql://postgres@localhost:5432/agrotrace_db
SECRET_KEY=<chave gerada com secrets.token_hex(32)>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

API em `http://127.0.0.1:8000` e docs em `/docs`.

**Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

App em `http://localhost:3000`.

## Observações

- Sempre usar `python -m pip` (e não `pip`) com o venv ativo.
- Manter `bcrypt==4.0.1` (compatibilidade com passlib).
- O primeiro usuário admin precisa ser criado direto no banco;
  os demais são cadastrados via `POST /auth/register`.