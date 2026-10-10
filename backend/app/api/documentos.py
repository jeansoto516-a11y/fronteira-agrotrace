import os
import uuid
import shutil
from datetime import date, timedelta

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Form,
)
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.config import settings
from app.models.usuario import Usuario, PerfilUsuario
from app.models.documento import (
    Documento, TipoDocumento, EntidadeDocumento,
)
from app.models.fazenda import Fazenda
from app.models.talhao import Talhao
from app.schemas.documento import DocumentoOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/documentos", tags=["Documentos"])

EXTENSOES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}
ADMIN = PerfilUsuario.COOPERATIVA_ADMIN


def _salvar_arquivo(arquivo: UploadFile) -> str:
    ext = os.path.splitext(arquivo.filename)[1].lower()
    if ext not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de arquivo não permitido",
        )
    os.makedirs(settings.PASTA_UPLOADS, exist_ok=True)
    caminho = os.path.join(settings.PASTA_UPLOADS, f"{uuid.uuid4()}{ext}")
    with open(caminho, "wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)
    return caminho


def _buscar_ou_404(db: Session, documento_id: uuid.UUID) -> Documento:
    doc = db.query(Documento).filter(Documento.id == documento_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado",
        )
    return doc


@router.get("/vencendo", response_model=list[DocumentoOut])
def listar_vencendo(
    dias: int = 30,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Vigentes vencidos ou que vencem em até N dias."""
    limite = date.today() + timedelta(days=dias)
    return (
        db.query(Documento)
        .filter(Documento.vigente.is_(True))
        .filter(Documento.data_validade.isnot(None))
        .filter(Documento.data_validade <= limite)
        .order_by(Documento.data_validade.asc())
        .all()
    )


@router.get("/grupo/{grupo_id}/versoes", response_model=list[DocumentoOut])
def listar_versoes(
    grupo_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    return (
        db.query(Documento)
        .filter(Documento.grupo_id == grupo_id)
        .order_by(Documento.versao.desc())
        .all()
    )


@router.post(
    "/", response_model=DocumentoOut,
    status_code=status.HTTP_201_CREATED,
)
def enviar_documento(
    tipo: TipoDocumento = Form(...),
    entidade_tipo: EntidadeDocumento = Form(...),
    entidade_id: uuid.UUID = Form(...),
    data_validade: date | None = Form(None),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    if entidade_tipo == EntidadeDocumento.FAZENDA:
        modelo, nome = Fazenda, "Fazenda"
    else:
        modelo, nome = Talhao, "Talhão"
    if not db.query(modelo).filter(modelo.id == entidade_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{nome} não encontrado(a)",
        )

    caminho = _salvar_arquivo(arquivo)
    novo_id = uuid.uuid4()
    novo = Documento(
        id=novo_id,
        grupo_id=novo_id,
        versao=1,
        vigente=True,
        tipo=tipo,
        entidade_tipo=entidade_tipo,
        entidade_id=entidade_id,
        nome_arquivo_original=arquivo.filename,
        caminho_arquivo=caminho,
        data_validade=data_validade,
        enviado_por_id=usuario_atual.id,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Documento",
        usuario_id=usuario_atual.id, entidade_id=novo.id,
        detalhes=f"Documento {tipo.value} v1 enviado "
                 f"({arquivo.filename})",
    )
    return novo


@router.post(
    "/{documento_id}/nova-versao", response_model=DocumentoOut,
    status_code=status.HTTP_201_CREATED,
)
def nova_versao(
    documento_id: uuid.UUID,
    data_validade: date | None = Form(None),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    base = _buscar_ou_404(db, documento_id)
    caminho = _salvar_arquivo(arquivo)

    maior = (
        db.query(func.max(Documento.versao))
        .filter(Documento.grupo_id == base.grupo_id)
        .scalar()
    )
    (
        db.query(Documento)
        .filter(Documento.grupo_id == base.grupo_id)
        .update({"vigente": False})
    )
    nova = Documento(
        id=uuid.uuid4(),
        grupo_id=base.grupo_id,
        versao=(maior or 0) + 1,
        vigente=True,
        tipo=base.tipo,
        entidade_tipo=base.entidade_tipo,
        entidade_id=base.entidade_id,
        nome_arquivo_original=arquivo.filename,
        caminho_arquivo=caminho,
        data_validade=data_validade,
        enviado_por_id=usuario_atual.id,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Documento",
        usuario_id=usuario_atual.id, entidade_id=nova.id,
        detalhes=f"Nova versão v{nova.versao} do documento "
                 f"{base.tipo.value} (grupo {base.grupo_id})",
    )
    return nova


@router.get("/", response_model=list[DocumentoOut])
def listar_documentos(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    entidade_tipo: EntidadeDocumento | None = None,
    entidade_id: uuid.UUID | None = None,
    incluir_historico: bool = False,
):
    query = db.query(Documento)
    if not incluir_historico:
        query = query.filter(Documento.vigente.is_(True))
    if entidade_tipo:
        query = query.filter(Documento.entidade_tipo == entidade_tipo)
    if entidade_id:
        query = query.filter(Documento.entidade_id == entidade_id)
    return query.order_by(Documento.criado_em.desc()).all()


@router.get("/{documento_id}/download")
def baixar_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    doc = _buscar_ou_404(db, documento_id)
    if not os.path.exists(doc.caminho_arquivo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado em disco",
        )
    return FileResponse(
        path=doc.caminho_arquivo,
        filename=doc.nome_arquivo_original,
    )


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    doc = _buscar_ou_404(db, documento_id)

    if doc.vigente:
        anterior = (
            db.query(Documento)
            .filter(Documento.grupo_id == doc.grupo_id)
            .filter(Documento.id != doc.id)
            .order_by(Documento.versao.desc())
            .first()
        )
        if anterior:
            anterior.vigente = True

    if os.path.exists(doc.caminho_arquivo):
        os.remove(doc.caminho_arquivo)

    nome = doc.nome_arquivo_original
    versao = doc.versao
    db.delete(doc)
    db.commit()

    registrar_log(
        db, acao=TipoAcao.EXCLUIR, entidade="Documento",
        usuario_id=usuario_atual.id, entidade_id=documento_id,
        detalhes=f"Documento {nome} (v{versao}) excluído",
    )
    return None