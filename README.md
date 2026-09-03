# Fronteira AgroTrace

Plataforma de rastreabilidade de commodities agrícolas — do talhão até a exportação — com geolocalização de áreas produtivas e gestão de certificação socioambiental, atendendo exigências de compradores internacionais (ex: regulamentações anti-desmatamento tipo EUDR).

**Cliente:** Sertões Agroexportadora — cooperativa exportadora de soja e café com atuação em MT e BA.

## Objetivo

Substituir o controle de origem da produção (hoje feito em planilhas soltas por fazenda) por uma plataforma centralizada com rastreabilidade real da cadeia, cruzamento geoespacial com áreas embargadas/desmatamento, e visibilidade sobre a documentação socioambiental de cada lote antes do embarque.

## Stack técnica

**Backend**
- Python + FastAPI
- SQLAlchemy + GeoAlchemy2 + Alembic (migrations)
- PostgreSQL + PostGIS

**Frontend**
- Next.js (React) + TypeScript
- react-leaflet (mapas)
- shadcn/ui (UI Kit)

**Outros**
- Autenticação: JWT + refresh token (python-jose + passlib)
- Relatórios em PDF: WeasyPrint
- Armazenamento de documentos: disco local (sem deploy neste projeto)

## Escopo funcional

1. Cadastro de produtores rurais, fazendas e talhões (com polígono georreferenciado)
2. Cadastro de safras e vínculo talhão → safra → cultura
3. Registro de coleta/colheita por talhão com geolocalização e data
4. Formação de lotes com rastreabilidade reversa até o talhão de origem
5. Gestão documental de certificações socioambientais (CAR, licenças, laudos)
6. Cruzamento geoespacial com áreas embargadas/desmatamento (ST_Intersects)
7. Cadeia de custódia: fazenda → armazém → transporte → porto → exportação
8. Painel de conformidade por lote
9. Relatório de rastreabilidade em PDF (com mapa embutido)
10. Perfis de acesso: Produtor, Cooperativa/Admin, Auditor de Compliance, Exportador
11. Dashboard executivo com indicadores consolidados

## Estrutura do repositório

fronteira-agrotrace/
├── backend/ # API FastAPI + SQLAlchemy + GeoAlchemy2 + Alembic
├── frontend/ # Next.js + TypeScript + shadcn/ui + react-leaflet
├── docs/ # Documentação técnica do projeto
└── README.md


## Status do projeto

🚧 Em desenvolvimento — seguindo cronograma de 16 semanas dividido em 16 fases.

**Fase 1 — Setup & Infraestrutura (Semana 1-2):** ✅ Backend inicial configurado (FastAPI + PostgreSQL + PostGIS + Alembic). Em andamento: estrutura de repositório Git.

## Como rodar o backend localmente

\`\`\`powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
\`\`\`

API disponível em `http://127.0.0.1:8000`, documentação automática em `http://127.0.0.1:8000/docs`.