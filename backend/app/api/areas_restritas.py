import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.db.database import get_db
from app.core.deps import get_usuario_atual
from app.models.usuario import Usuario
from app.models.area_restrita import AreaRestrita, TipoAreaRestrita
from app.schemas.area_restrita import AreaRestritaOut

router = APIRouter(prefix="/areas-restritas", tags=["Áreas restritas"])


def _area_para_saida(area: AreaRestrita) -> dict:
    """Converte a área do banco (geometria PostGIS) em dict com GeoJSON."""
    area_hectares = None
    if area.area_calculada_m2 is not None:
        area_hectares = round(area.area_calculada_m2 / 10_000, 4)

    return {
        "id": area.id,
        "tipo": area.tipo,
        "identificador": area.identificador,
        "descricao": area.descricao,
        "fonte": area.fonte,
        "data_referencia": area.data_referencia,
        "criado_em": area.criado_em,
        "area_hectares": area_hectares,
        "geometria": mapping(to_shape(area.geometria)),
    }


@router.get("/", response_model=list[AreaRestritaOut])
def listar_areas_restritas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    tipo: TipoAreaRestrita | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Lista as áreas embargadas / de desmatamento, com filtro por tipo."""
    query = db.query(AreaRestrita)
    if tipo:
        query = query.filter(AreaRestrita.tipo == tipo)
    areas = (
        query.order_by(AreaRestrita.data_referencia.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_area_para_saida(a) for a in areas]


@router.get("/{area_id}", response_model=AreaRestritaOut)
def buscar_area_restrita(
    area_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Busca uma área específica pelo ID."""
    area = db.query(AreaRestrita).filter(AreaRestrita.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área não encontrada",
        )
    return _area_para_saida(area)