import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from geoalchemy2 import WKTElement

from app.db.database import get_db
from app.core.deps import get_usuario_atual
from app.models.usuario import Usuario
from app.models.colheita import Colheita
from app.models.talhao_safra import TalhaoSafra
from app.schemas.colheita import ColheitaCreate, ColheitaOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/colheitas", tags=["Colheitas"])


def _colheita_para_saida(colheita: Colheita) -> dict:
    """Converte uma Colheita do banco (com campo geoespacial) para latitude/longitude simples."""
    ponto = to_shape(colheita.localizacao_coleta)
    return {
        "id": colheita.id,
        "data_colheita": colheita.data_colheita,
        "quantidade_kg": colheita.quantidade_kg,
        "latitude": ponto.y,
        "longitude": ponto.x,
        "talhao_safra_id": colheita.talhao_safra_id,
        "criado_em": colheita.criado_em,
    }


@router.post("/", response_model=ColheitaOut, status_code=status.HTTP_201_CREATED)
def registrar_colheita(
    dados: ColheitaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """
    Registra um evento de colheita/coleta com geolocalização e data/hora.
    Qualquer perfil autenticado pode registrar (ex: um Produtor no campo).
    """
    talhao_safra = db.query(TalhaoSafra).filter(TalhaoSafra.id == dados.talhao_safra_id).first()
    if not talhao_safra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vínculo talhão-safra não encontrado")

    localizacao = WKTElement(f"POINT({dados.longitude} {dados.latitude})", srid=4326)

    nova_colheita = Colheita(
        data_colheita=dados.data_colheita,
        quantidade_kg=dados.quantidade_kg,
        localizacao_coleta=localizacao,
        talhao_safra_id=dados.talhao_safra_id,
    )
    db.add(nova_colheita)
    db.commit()
    db.refresh(nova_colheita)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Colheita", usuario_id=usuario_atual.id,
        entidade_id=nova_colheita.id,
        detalhes=f"Colheita de {nova_colheita.quantidade_kg}kg registrada em {nova_colheita.data_colheita}",
    )

    return _colheita_para_saida(nova_colheita)


@router.get("/", response_model=list[ColheitaOut])
def listar_colheitas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    talhao_safra_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Lista colheitas registradas, com filtro opcional por vínculo talhão-safra."""
    query = db.query(Colheita)
    if talhao_safra_id:
        query = query.filter(Colheita.talhao_safra_id == talhao_safra_id)
    colheitas = query.order_by(Colheita.data_colheita.desc()).offset(skip).limit(limit).all()
    return [_colheita_para_saida(c) for c in colheitas]


@router.get("/{colheita_id}", response_model=ColheitaOut)
def buscar_colheita(
    colheita_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Busca uma colheita específica pelo ID."""
    colheita = db.query(Colheita).filter(Colheita.id == colheita_id).first()
    if not colheita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colheita não encontrada")
    return _colheita_para_saida(colheita)