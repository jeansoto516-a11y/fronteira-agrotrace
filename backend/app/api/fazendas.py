import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from geoalchemy2 import WKTElement

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.fazenda import Fazenda
from app.models.produtor import Produtor
from app.schemas.fazenda import FazendaCreate, FazendaUpdate, FazendaOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/fazendas", tags=["Fazendas"])


def _fazenda_para_saida(fazenda: Fazenda) -> dict:
    """
    Converte uma Fazenda do banco (com campo geoespacial) para um
    dicionário com latitude/longitude simples, prontos para o schema
    FazendaOut. Necessário porque o Pydantic não sabe ler um tipo
    Geometry do PostGIS diretamente.
    """
    lat, lon = None, None
    if fazenda.localizacao is not None:
        ponto = to_shape(fazenda.localizacao)  # converte para objeto Shapely
        lat, lon = ponto.y, ponto.x  # Shapely usa (x=longitude, y=latitude)

    return {
        "id": fazenda.id,
        "nome": fazenda.nome,
        "municipio": fazenda.municipio,
        "estado": fazenda.estado,
        "area_total_hectares": fazenda.area_total_hectares,
        "latitude": lat,
        "longitude": lon,
        "produtor_id": fazenda.produtor_id,
        "criado_em": fazenda.criado_em,
    }


@router.post("/", response_model=FazendaOut, status_code=status.HTTP_201_CREATED)
def criar_fazenda(
    dados: FazendaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Cadastra uma fazenda vinculada a um produtor existente. Restrito a Cooperativa/Admin."""
    produtor = db.query(Produtor).filter(Produtor.id == dados.produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produtor não encontrado")

    localizacao = None
    if dados.latitude is not None and dados.longitude is not None:
        # WKTElement: formato de texto que o PostGIS entende para
        # representar um ponto geográfico. SRID 4326 = padrão GPS.
        localizacao = WKTElement(f"POINT({dados.longitude} {dados.latitude})", srid=4326)

    nova_fazenda = Fazenda(
        nome=dados.nome,
        municipio=dados.municipio,
        estado=dados.estado,
        area_total_hectares=dados.area_total_hectares,
        produtor_id=dados.produtor_id,
        localizacao=localizacao,
    )
    db.add(nova_fazenda)
    db.commit()
    db.refresh(nova_fazenda)

    registrar_log(
        db,
        acao=TipoAcao.CRIAR,
        entidade="Fazenda",
        usuario_id=usuario_atual.id,
        entidade_id=nova_fazenda.id,
        detalhes=f"Fazenda {nova_fazenda.nome} cadastrada para produtor {produtor.nome}",
    )

    return _fazenda_para_saida(nova_fazenda)


@router.get("/", response_model=list[FazendaOut])
def listar_fazendas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    produtor_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Lista fazendas, com filtro opcional por produtor."""
    query = db.query(Fazenda)
    if produtor_id:
        query = query.filter(Fazenda.produtor_id == produtor_id)
    fazendas = query.offset(skip).limit(limit).all()
    return [_fazenda_para_saida(f) for f in fazendas]


@router.get("/{fazenda_id}", response_model=FazendaOut)
def buscar_fazenda(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Busca uma fazenda específica pelo ID."""
    fazenda = db.query(Fazenda).filter(Fazenda.id == fazenda_id).first()
    if not fazenda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fazenda não encontrada")
    return _fazenda_para_saida(fazenda)


@router.put("/{fazenda_id}", response_model=FazendaOut)
def editar_fazenda(
    fazenda_id: uuid.UUID,
    dados: FazendaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Edita os dados de uma fazenda existente. Restrito a Cooperativa/Admin."""
    fazenda = db.query(Fazenda).filter(Fazenda.id == fazenda_id).first()
    if not fazenda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fazenda não encontrada")

    dados_atualizados = dados.model_dump(exclude_unset=True)

    # Latitude/longitude precisam de tratamento especial, já que não
    # existem como colunas diretas no model (viram o campo 'localizacao').
    nova_lat = dados_atualizados.pop("latitude", None)
    nova_lon = dados_atualizados.pop("longitude", None)
    if nova_lat is not None and nova_lon is not None:
        fazenda.localizacao = WKTElement(f"POINT({nova_lon} {nova_lat})", srid=4326)

    for campo, valor in dados_atualizados.items():
        setattr(fazenda, campo, valor)

    db.commit()
    db.refresh(fazenda)

    registrar_log(
        db,
        acao=TipoAcao.EDITAR,
        entidade="Fazenda",
        usuario_id=usuario_atual.id,
        entidade_id=fazenda.id,
        detalhes=f"Fazenda {fazenda.nome} editada",
    )

    return _fazenda_para_saida(fazenda)


@router.delete("/{fazenda_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_fazenda(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Exclui uma fazenda. Restrito a Cooperativa/Admin."""
    fazenda = db.query(Fazenda).filter(Fazenda.id == fazenda_id).first()
    if not fazenda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fazenda não encontrada")

    nome_fazenda = fazenda.nome
    db.delete(fazenda)
    db.commit()

    registrar_log(
        db,
        acao=TipoAcao.EXCLUIR,
        entidade="Fazenda",
        usuario_id=usuario_atual.id,
        entidade_id=fazenda_id,
        detalhes=f"Fazenda {nome_fazenda} excluída",
    )

    return None