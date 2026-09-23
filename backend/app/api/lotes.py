import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import mapping
from geoalchemy2.shape import to_shape

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.lote import Lote
from app.models.lote_colheita import LoteColheita
from app.models.colheita import Colheita
from app.schemas.lote import (
    LoteCreate,
    LoteOut,
    RastreabilidadeLote,
    ColheitaRastreada,
    OrigemTalhao,
    OrigemFazenda,
    OrigemProdutor,
)
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/lotes", tags=["Lotes"])


@router.post("/", response_model=LoteOut, status_code=status.HTTP_201_CREATED)
def criar_lote(
    dados: LoteCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """
    Forma um novo lote, agrupando uma ou mais colheitas (possivelmente
    de talhões diferentes). Restrito a Cooperativa/Admin.
    """
    codigo_existente = db.query(Lote).filter(Lote.codigo_lote == dados.codigo_lote).first()
    if codigo_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um lote com esse código")

    peso_total = 0.0
    vinculos_para_criar = []

    for item in dados.colheitas:
        colheita = db.query(Colheita).filter(Colheita.id == item.colheita_id).first()
        if not colheita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Colheita {item.colheita_id} não encontrada",
            )
        vinculos_para_criar.append((colheita, item.quantidade_kg))
        peso_total += item.quantidade_kg

    novo_lote = Lote(codigo_lote=dados.codigo_lote, peso_total_kg=peso_total)
    db.add(novo_lote)
    db.flush()  # garante que novo_lote.id já existe, sem precisar commitar ainda

    for colheita, quantidade in vinculos_para_criar:
        vinculo = LoteColheita(
            lote_id=novo_lote.id,
            colheita_id=colheita.id,
            quantidade_kg=quantidade,
        )
        db.add(vinculo)

    db.commit()
    db.refresh(novo_lote)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Lote", usuario_id=usuario_atual.id,
        entidade_id=novo_lote.id,
        detalhes=f"Lote {novo_lote.codigo_lote} formado com {len(vinculos_para_criar)} colheita(s), {peso_total}kg",
    )

    return novo_lote


@router.get("/", response_model=list[LoteOut])
def listar_lotes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Lista todos os lotes formados."""
    return db.query(Lote).all()


@router.get("/{lote_id}/rastreabilidade", response_model=RastreabilidadeLote)
def consultar_rastreabilidade(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """
    Rastreabilidade reversa: a partir de um Lote, retorna todas as
    Colheitas que o compõem, e para cada uma, o Talhão, Fazenda e
    Produtor de origem. É o núcleo do sistema de rastreabilidade.
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")

    origens = []
    for vinculo in lote.colheitas_vinculadas:
        colheita = vinculo.colheita
        talhao_safra = colheita.talhao_safra
        talhao = talhao_safra.talhao
        fazenda = talhao.fazenda
        produtor = fazenda.produtor

        origens.append(
            ColheitaRastreada(
                colheita_id=colheita.id,
                data_colheita=colheita.data_colheita,
                quantidade_kg_no_lote=vinculo.quantidade_kg,
                safra=talhao_safra.safra.identificacao,
                cultura=talhao_safra.cultura.nome,
                talhao=OrigemTalhao(
                    talhao_id=talhao.id,
                    nome_identificador=talhao.nome_identificador,
                    area_hectares=talhao.area_hectares,
                    poligono=mapping(to_shape(talhao.poligono)),
                ),
                fazenda=OrigemFazenda(
                    fazenda_id=fazenda.id,
                    nome=fazenda.nome,
                    municipio=fazenda.municipio,
                    estado=fazenda.estado,
                ),
                produtor=OrigemProdutor(
                    produtor_id=produtor.id,
                    nome=produtor.nome,
                    cpf_cnpj=produtor.cpf_cnpj,
                ),
            )
        )

    return RastreabilidadeLote(
        lote_id=lote.id,
        codigo_lote=lote.codigo_lote,
        peso_total_kg=lote.peso_total_kg,
        origens=origens,
    )