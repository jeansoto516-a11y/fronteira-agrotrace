import os
import uuid
import shutil
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.config import settings
from app.models.usuario import Usuario, PerfilUsuario
from app.models.documento import Documento, TipoDocumento, EntidadeDocumento
from app.models.fazenda import Fazenda
from app.models.talhao import Talhao
from app.schemas.documento import DocumentoOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/documentos", tags=["Documentos"])

# Extensões permitidas, para evitar upload de arquivos potencialmente perigosos.
EXTENSOES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}


@router.post("/", response_model=DocumentoOut, status_code=status.HTTP_201_CREATED)
def enviar_documento(
    tipo: TipoDocumento = Form(...),
    entidade_tipo: EntidadeDocumento = Form(...),
    entidade_id: uuid.UUID = Form(...),
    data_validade: date | None = Form(None),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """
    Envia um documento de certificação (CAR, licença, laudo), vinculado
    a uma Fazenda ou Talhão. Restrito a Cooperativa/Admin.
    """
    # Valida se a entidade referenciada realmente existe
    if entidade_tipo == EntidadeDocumento.FAZENDA:
        entidade = db.query(Fazenda).filter(Fazenda.id == entidade_id).first()
        if not entidade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fazenda não encontrada")
    else:
        entidade = db.query(Talhao).filter(Talhao.id == entidade_id).first()
        if not entidade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talhão não encontrado")

    extensao = os.path.splitext(arquivo.filename)[1].lower()
    if extensao not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido. Aceitos: {', '.join(EXTENSOES_PERMITIDAS)}",
        )

    # Nome de arquivo único em disco, para evitar sobrescrever arquivos
    # com nomes repetidos enviados por pessoas diferentes.
    nome_no_disco = f"{uuid.uuid4()}{extensao}"
    os.makedirs(settings.PASTA_UPLOADS, exist_ok=True)
    caminho_completo = os.path.join(settings.PASTA_UPLOADS, nome_no_disco)

    with open(caminho_completo, "wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)

    novo_documento = Documento(
        tipo=tipo,
        entidade_tipo=entidade_tipo,
        entidade_id=entidade_id,
        nome_arquivo_original=arquivo.filename,
        caminho_arquivo=caminho_completo,
        data_validade=data_validade,
        enviado_por_id=usuario_atual.id,
    )
    db.add(novo_documento)
    db.commit()
    db.refresh(novo_documento)

    registrar_log(
        db, acao=TipoAcao.CRIAR, entidade="Documento", usuario_id=usuario_atual.id,
        entidade_id=novo_documento.id,
        detalhes=f"Documento {tipo.value} ({arquivo.filename}) enviado para {entidade_tipo.value} {entidade_id}",
    )

    return novo_documento


@router.get("/", response_model=list[DocumentoOut])
def listar_documentos(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    entidade_tipo: EntidadeDocumento | None = None,
    entidade_id: uuid.UUID | None = None,
):
    """Lista documentos, com filtro opcional por entidade (fazenda ou talhão)."""
    query = db.query(Documento)
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
    """Baixa o arquivo físico de um documento."""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")

    if not os.path.exists(documento.caminho_arquivo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado em disco")

    return FileResponse(
        path=documento.caminho_arquivo,
        filename=documento.nome_arquivo_original,
    )


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_documento(
    documento_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Exclui um documento (registro + arquivo físico). Restrito a Cooperativa/Admin."""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")

    if os.path.exists(documento.caminho_arquivo):
        os.remove(documento.caminho_arquivo)

    nome_arquivo = documento.nome_arquivo_original
    db.delete(documento)
    db.commit()

    registrar_log(
        db, acao=TipoAcao.EXCLUIR, entidade="Documento", usuario_id=usuario_atual.id,
        entidade_id=documento_id, detalhes=f"Documento {nome_arquivo} excluído",
    )

    return None