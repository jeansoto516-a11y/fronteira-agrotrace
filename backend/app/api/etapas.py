import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao
from app.models.usuario import Usuario, PerfilUsuario
from app.models.lote import Lote
from app.models.etapa_lote import EtapaLote, TipoEtapa
from app.schemas.etapa import (
    EtapaLoteCreate,
    EtapaLoteUpdate,
    EtapaLoteOut,
    validar_regras_do_tipo,
)

router = APIRouter(tags=["Etapas"])

# Perfis que podem cadastrar/corrigir etapas. Todos os usuários
# logados podem consultar.
ESCRITA = (PerfilUsuario.COOPERATIVA_ADMIN, PerfilUsuario.EXPORTADOR)

CAMPOS_EDITAVEIS = list(EtapaLoteUpdate.model_fields.keys())


def _lote_ou_404(db: Session, lote_id: uuid.UUID) -> Lote:
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote não encontrado",
        )
    return lote


def _etapa_ou_404(db: Session, etapa_id: uuid.UUID) -> EtapaLote:
    etapa = db.query(EtapaLote).filter(EtapaLote.id == etapa_id).first()
    if not etapa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada",
        )
    return etapa


@router.post(
    "/lotes/{lote_id}/etapas",
    response_model=EtapaLoteOut,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_etapa(
    lote_id: uuid.UUID,
    dados: EtapaLoteCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(*ESCRITA)),
):
    """Cadastra uma etapa no final da cadeia do lote (ordem automática)."""
    lote = _lote_ou_404(db, lote_id)

    ja_exporta = (
        db.query(EtapaLote.id)
        .filter(EtapaLote.lote_id == lote.id)
        .filter(EtapaLote.tipo == TipoEtapa.EXPORTACAO)
        .first()
    )
    if ja_exporta:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Este lote já tem etapa de exportação, que encerra a "
                "cadeia: nenhuma etapa pode ser cadastrada depois dela"
            ),
        )

    maior = (
        db.query(func.max(EtapaLote.ordem))
        .filter(EtapaLote.lote_id == lote.id)
        .scalar()
    )
    etapa = EtapaLote(
        lote_id=lote.id,
        ordem=(maior or 0) + 1,
        **dados.model_dump(),
    )
    db.add(etapa)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outra etapa foi cadastrada ao mesmo tempo. Tente novamente",
        )
    db.refresh(etapa)

    registrar_log(
        db,
        acao=TipoAcao.CRIAR,
        entidade="EtapaLote",
        usuario_id=usuario_atual.id,
        entidade_id=etapa.id,
        detalhes=(
            f"Etapa {etapa.tipo.value} (ordem {etapa.ordem}) cadastrada "
            f"no lote {lote.codigo_lote}"
        ),
    )
    return etapa


@router.get("/lotes/{lote_id}/etapas", response_model=list[EtapaLoteOut])
def listar_etapas_do_lote(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Etapas registradas do lote, em ordem (sem a etapa de origem)."""
    lote = _lote_ou_404(db, lote_id)
    return (
        db.query(EtapaLote)
        .filter(EtapaLote.lote_id == lote.id)
        .order_by(EtapaLote.ordem)
        .all()
    )


@router.get("/etapas/{etapa_id}", response_model=EtapaLoteOut)
def buscar_etapa(
    etapa_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    return _etapa_ou_404(db, etapa_id)


@router.patch("/etapas/{etapa_id}", response_model=EtapaLoteOut)
def corrigir_etapa(
    etapa_id: uuid.UUID,
    dados: EtapaLoteUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(*ESCRITA)),
):
    """
    Corrige dados cadastrais da etapa. Responsável, status e datas
    mudam apenas por movimentação.
    """
    etapa = _etapa_ou_404(db, etapa_id)

    novos = dados.model_dump(exclude_unset=True)
    if not novos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo informado para alterar",
        )

    # Revalida as regras do tipo sobre o resultado final (existente + novo)
    resultado = {campo: getattr(etapa, campo) for campo in CAMPOS_EDITAVEIS}
    resultado.update(novos)
    erros = validar_regras_do_tipo(etapa.tipo, resultado)
    if erros:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=erros,
        )

    for campo, valor in novos.items():
        setattr(etapa, campo, valor)
    db.commit()
    db.refresh(etapa)

    registrar_log(
        db,
        acao=TipoAcao.EDITAR,
        entidade="EtapaLote",
        usuario_id=usuario_atual.id,
        entidade_id=etapa.id,
        detalhes=(
            f"Etapa {etapa.tipo.value} (ordem {etapa.ordem}) corrigida: "
            + ", ".join(sorted(novos.keys()))
        ),
    )
    return etapa