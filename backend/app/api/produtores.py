import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.models.usuario import Usuario, PerfilUsuario
from app.models.produtor import Produtor
from app.schemas.produtor import ProdutorCreate, ProdutorUpdate, ProdutorOut
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao

router = APIRouter(prefix="/produtores", tags=["Produtores"])


@router.post("/", response_model=ProdutorOut, status_code=status.HTTP_201_CREATED)
def criar_produtor(
    dados: ProdutorCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Cadastra um novo produtor rural. Restrito a Cooperativa/Admin."""
    existente = db.query(Produtor).filter(Produtor.cpf_cnpj == dados.cpf_cnpj).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um produtor cadastrado com esse CPF/CNPJ",
        )

    novo_produtor = Produtor(**dados.model_dump())
    db.add(novo_produtor)
    db.commit()
    db.refresh(novo_produtor)

    registrar_log(
        db,
        acao=TipoAcao.CRIAR,
        entidade="Produtor",
        usuario_id=usuario_atual.id,
        entidade_id=novo_produtor.id,
        detalhes=f"Produtor {novo_produtor.nome} cadastrado",
    )

    return novo_produtor


@router.get("/", response_model=list[ProdutorOut])
def listar_produtores(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
    skip: int = 0,
    limit: int = 100,
):
    """Lista todos os produtores cadastrados. Qualquer perfil autenticado pode consultar."""
    return db.query(Produtor).offset(skip).limit(limit).all()


@router.get("/{produtor_id}", response_model=ProdutorOut)
def buscar_produtor(
    produtor_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Busca um produtor específico pelo ID."""
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produtor não encontrado")
    return produtor


@router.put("/{produtor_id}", response_model=ProdutorOut)
def editar_produtor(
    produtor_id: uuid.UUID,
    dados: ProdutorUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Edita os dados de um produtor existente. Restrito a Cooperativa/Admin."""
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produtor não encontrado")

    dados_atualizados = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_atualizados.items():
        setattr(produtor, campo, valor)

    db.commit()
    db.refresh(produtor)

    registrar_log(
        db,
        acao=TipoAcao.EDITAR,
        entidade="Produtor",
        usuario_id=usuario_atual.id,
        entidade_id=produtor.id,
        detalhes=f"Produtor {produtor.nome} editado",
    )

    return produtor


@router.delete("/{produtor_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produtor(
    produtor_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(PerfilUsuario.COOPERATIVA_ADMIN)),
):
    """Exclui um produtor. Restrito a Cooperativa/Admin."""
    produtor = db.query(Produtor).filter(Produtor.id == produtor_id).first()
    if not produtor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produtor não encontrado")

    nome_produtor = produtor.nome
    db.delete(produtor)
    db.commit()

    registrar_log(
        db,
        acao=TipoAcao.EXCLUIR,
        entidade="Produtor",
        usuario_id=usuario_atual.id,
        entidade_id=produtor_id,
        detalhes=f"Produtor {nome_produtor} excluído",
    )

    return None