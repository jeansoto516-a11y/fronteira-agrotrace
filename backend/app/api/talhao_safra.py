import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.talhao_safra import TalhaoSafra
from app.models.talhao import Talhao
from app.models.safra import Safra
from app.models.cultura import Cultura
from app.schemas.talhao_safra import TalhaoSafraCreate, TalhaoSafraOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao
from app.api.talhoes import _talhao_para_saida

router = APIRouter(prefix="/talhao-safra", tags=["Vínculo Talhão-Safra-Cultura"])


@router.post("/", response_model=TalhaoSafraOut, status_code=status.HTTP_201_CREATED)
def vincular_talhao_safra_cultura(
    dados: TalhaoSafraCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """
    Vincula um talhão a uma safra e uma cultura, representando
    "este talhão, nesta safra, plantou esta cultura".
    """
    talhao = db.query(Talhao).filter(Talhao.id == dados.talhao_id).first()
    if not talhao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talhão não encontrado")

    safra = db.query(Safra).filter(Safra.id == dados.safra_id).first()
    if not safra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safra não encontrada")

    cultura = db.query(Cultura).filter(Cultura.id == dados.cultura_id).first()
    if not cultura:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultura não encontrada")

    # Evita duplicar o mesmo vínculo (mesmo talhão + mesma safra já registrado)
    vinculo_existente = (
        db.query(TalhaoSafra)
        .filter(TalhaoSafra.talhao_id == dados.talhao_id, TalhaoSafra.safra_id == dados.safra_id)
        .first()
    )
    if vinculo_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este talhão já está vinculado a esta safra",
        )

    novo_vinculo = TalhaoSafra(
        talhao_id=dados.talhao_id,
        safra_id=dados.safra_id,
        cultura_id=dados.cultura_id,
    )
    db.add(novo_vinculo)
    db.commit()
    db.refresh(novo_vinculo)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="TalhaoSafra", usuario_id=usuario_atual.id,
        entidade_id=novo_vinculo.id,
        detalhes=f"Talhão {talhao.nome_identificador} vinculado à safra {safra.identificacao} com cultura {cultura.nome}",
    )

    return {
        "id": novo_vinculo.id,
        "talhao": _talhao_para_saida(talhao),
        "safra": safra,
        "cultura": cultura,
    }


@router.get("/", response_model=list[TalhaoSafraOut])
def listar_vinculos(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    talhao_id: uuid.UUID | None = None,
    safra_id: uuid.UUID | None = None,
):
    """Lista vínculos talhão-safra-cultura, com filtros opcionais."""
    query = db.query(TalhaoSafra)
    if talhao_id:
        query = query.filter(TalhaoSafra.talhao_id == talhao_id)
    if safra_id:
        query = query.filter(TalhaoSafra.safra_id == safra_id)
        vinculos = query.all()
    return [
        {
            "id": v.id,
            "talhao": _talhao_para_saida(v.talhao),
            "safra": v.safra,
            "cultura": v.cultura,
        }
        for v in vinculos
    ]