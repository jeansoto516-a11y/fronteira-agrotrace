import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import shape, mapping
from geoalchemy2 import WKTElement

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.talhao import Talhao
from app.models.fazenda import Fazenda
from app.schemas.talhao import TalhaoCreate, TalhaoUpdate, TalhaoOut, GeoJSONPolygon
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/talhoes", tags=["Talhões"])


def _geojson_para_wkt(poligono: GeoJSONPolygon) -> WKTElement:
    """
    Converte um polígono GeoJSON (formato que a API recebe) para
    WKTElement (formato que o PostGIS/GeoAlchemy2 armazena).
    """
    geometria_shapely = shape(poligono.model_dump())
    return WKTElement(geometria_shapely.wkt, srid=4326)


def _talhao_para_saida(talhao: Talhao) -> dict:
    """
    Converte um Talhão do banco (com campo geoespacial) para um
    dicionário com o polígono em formato GeoJSON, para o TalhaoOut.
    """
    poligono_shapely = to_shape(talhao.poligono)
    poligono_geojson = mapping(poligono_shapely)  # shapely -> dict GeoJSON

    return {
        "id": talhao.id,
        "nome_identificador": talhao.nome_identificador,
        "area_hectares": talhao.area_hectares,
        "fazenda_id": talhao.fazenda_id,
        "criado_em": talhao.criado_em,
        "poligono": poligono_geojson,
    }


@router.post("/", response_model=TalhaoOut, status_code=status.HTTP_201_CREATED)
def criar_talhao(
    dados: TalhaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Cadastra um talhão com polígono georreferenciado, vinculado a uma fazenda."""
    fazenda = db.query(Fazenda).filter(Fazenda.id == dados.fazenda_id).first()
    if not fazenda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fazenda não encontrada")

    novo_talhao = Talhao(
        nome_identificador=dados.nome_identificador,
        area_hectares=dados.area_hectares,
        fazenda_id=dados.fazenda_id,
        poligono=_geojson_para_wkt(dados.poligono),
    )
    db.add(novo_talhao)
    db.commit()
    db.refresh(novo_talhao)

    registrar_log(
        db,
        acao=TipoAcao.CRIAR,
        entidade="Talhao",
        usuario_id=usuario_atual.id,
        entidade_id=novo_talhao.id,
        detalhes=f"Talhão {novo_talhao.nome_identificador} cadastrado na fazenda {fazenda.nome}",
    )

    return _talhao_para_saida(novo_talhao)


@router.get("/", response_model=list[TalhaoOut])
def listar_talhoes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    fazenda_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Lista talhões, com filtro opcional por fazenda."""
    query = db.query(Talhao)
    if fazenda_id:
        query = query.filter(Talhao.fazenda_id == fazenda_id)
    talhoes = query.offset(skip).limit(limit).all()
    return [_talhao_para_saida(t) for t in talhoes]


@router.get("/{talhao_id}", response_model=TalhaoOut)
def buscar_talhao(
    talhao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Busca um talhão específico pelo ID."""
    talhao = db.query(Talhao).filter(Talhao.id == talhao_id).first()
    if not talhao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talhão não encontrado")
    return _talhao_para_saida(talhao)


@router.put("/{talhao_id}", response_model=TalhaoOut)
def editar_talhao(
    talhao_id: uuid.UUID,
    dados: TalhaoUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Edita os dados de um talhão existente. Restrito a Cooperativa/Admin."""
    talhao = db.query(Talhao).filter(Talhao.id == talhao_id).first()
    if not talhao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talhão não encontrado")

    dados_atualizados = dados.model_dump(exclude_unset=True)

    novo_poligono = dados_atualizados.pop("poligono", None)
    if novo_poligono is not None:
        talhao.poligono = _geojson_para_wkt(GeoJSONPolygon(**novo_poligono))

    for campo, valor in dados_atualizados.items():
        setattr(talhao, campo, valor)

    db.commit()
    db.refresh(talhao)

    registrar_log(
        db,
        acao=TipoAcao.EDITAR,
        entidade="Talhao",
        usuario_id=usuario_atual.id,
        entidade_id=talhao.id,
        detalhes=f"Talhão {talhao.nome_identificador} editado",
    )

    return _talhao_para_saida(talhao)


@router.delete("/{talhao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_talhao(
    talhao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Exclui um talhão. Restrito a Cooperativa/Admin."""
    talhao = db.query(Talhao).filter(Talhao.id == talhao_id).first()
    if not talhao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talhão não encontrado")

    nome_talhao = talhao.nome_identificador
    db.delete(talhao)
    db.commit()

    registrar_log(
        db,
        acao=TipoAcao.EXCLUIR,
        entidade="Talhao",
        usuario_id=usuario_atual.id,
        entidade_id=talhao_id,
        detalhes=f"Talhão {nome_talhao} excluído",
    )

    return None