import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual
from app.core.conformidade import (
    StatusConformidade,
    avaliar_lote,
    avaliar_todos,
)
from app.models.usuario import Usuario
from app.schemas.conformidade import (
    ConformidadeLoteOut,
    ResumoConformidadeOut,
)

router = APIRouter(tags=["Conformidade"])

# Mais grave primeiro, para a lista abrir pelo que exige atenção.
ORDEM_STATUS = {
    StatusConformidade.VENCIDO: 0,
    StatusConformidade.PENDENTE: 1,
    StatusConformidade.COMPLETO: 2,
}


@router.get(
    "/lotes/{lote_id}/conformidade", response_model=ConformidadeLoteOut
)
def conformidade_do_lote(
    lote_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Status de conformidade do lote, com os motivos."""
    avaliacao = avaliar_lote(db, lote_id)
    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote não encontrado",
        )
    return avaliacao


@router.get("/conformidade/lotes", response_model=list[ConformidadeLoteOut])
def listar_conformidade(
    status_conformidade: StatusConformidade | None = None,
    incluir_motivos: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Conformidade de todos os lotes (os mais graves primeiro)."""
    avaliacoes = avaliar_todos(db)
    if status_conformidade is not None:
        avaliacoes = [
            a for a in avaliacoes if a["status"] == status_conformidade
        ]
    avaliacoes.sort(key=lambda a: (ORDEM_STATUS[a["status"]], a["codigo_lote"]))
    if not incluir_motivos:
        avaliacoes = [{**a, "motivos": []} for a in avaliacoes]
    return avaliacoes


@router.get("/conformidade/resumo", response_model=ResumoConformidadeOut)
def resumo_conformidade(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Contadores para o dashboard."""
    avaliacoes = avaliar_todos(db)
    return ResumoConformidadeOut(
        total_lotes=len(avaliacoes),
        completos=sum(
            1 for a in avaliacoes if a["status"] == StatusConformidade.COMPLETO
        ),
        pendentes=sum(
            1 for a in avaliacoes if a["status"] == StatusConformidade.PENDENTE
        ),
        vencidos=sum(
            1 for a in avaliacoes if a["status"] == StatusConformidade.VENCIDO
        ),
        com_avisos=sum(1 for a in avaliacoes if a["total_avisos"] > 0),
    )