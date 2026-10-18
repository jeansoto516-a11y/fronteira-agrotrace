import uuid
from datetime import datetime, timezone

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
from app.models.etapa_lote import EtapaLote, StatusEtapa
from app.models.movimentacao_etapa import MovimentacaoEtapa, TipoMovimentacao
from app.schemas.movimentacao import MovimentacaoCreate, MovimentacaoOut

router = APIRouter(tags=["Movimentações"])

ESCRITA = (PerfilUsuario.COOPERATIVA_ADMIN, PerfilUsuario.EXPORTADOR)

# Tolerância para comparar quantidades em ponto flutuante
EPS = 1e-6


def _conflito(mensagem: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail=mensagem
    )


def _para_saida(mov: MovimentacaoEtapa, nome_revisor) -> MovimentacaoOut:
    return MovimentacaoOut(
        id=mov.id,
        etapa_id=mov.etapa_id,
        tipo=mov.tipo,
        ocorrida_em=mov.ocorrida_em,
        quantidade_kg=mov.quantidade_kg,
        responsavel=mov.responsavel,
        documento_referencia=mov.documento_referencia,
        observacao=mov.observacao,
        registrado_por_id=mov.registrado_por_id,
        registrado_por_nome=nome_revisor,
        criado_em=mov.criado_em,
    )


@router.post(
    "/etapas/{etapa_id}/movimentacoes",
    response_model=MovimentacaoOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_movimentacao(
    etapa_id: uuid.UUID,
    dados: MovimentacaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(*ESCRITA)),
):
    """
    Registra um evento na etapa e atualiza a etapa conforme o tipo:
    entrada → em andamento; saída → concluída; transferência → troca
    o responsável; ocorrência → apenas histórico.
    """
    # FOR UPDATE: trava a etapa até o commit, para dois registros
    # simultâneos não furarem as regras de quantidade.
    etapa = (
        db.query(EtapaLote)
        .filter(EtapaLote.id == etapa_id)
        .with_for_update()
        .first()
    )
    if not etapa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada",
        )
    lote = db.query(Lote).filter(Lote.id == etapa.lote_id).first()

    tipo = dados.tipo
    ocorrida_em = dados.ocorrida_em or datetime.now(timezone.utc)

    if tipo != TipoMovimentacao.OCORRENCIA and (
        etapa.status == StatusEtapa.CONCLUIDA
    ):
        raise _conflito(
            "Etapa já concluída: só é possível registrar ocorrências"
        )

    total_entradas = (
        db.query(func.coalesce(func.sum(MovimentacaoEtapa.quantidade_kg), 0.0))
        .filter(MovimentacaoEtapa.etapa_id == etapa.id)
        .filter(MovimentacaoEtapa.tipo == TipoMovimentacao.ENTRADA)
        .scalar()
    )

    if tipo == TipoMovimentacao.ENTRADA:
        anterior_pendente = (
            db.query(EtapaLote.id)
            .filter(EtapaLote.lote_id == etapa.lote_id)
            .filter(EtapaLote.ordem < etapa.ordem)
            .filter(EtapaLote.status != StatusEtapa.CONCLUIDA)
            .first()
        )
        if anterior_pendente:
            raise _conflito(
                "Há etapas anteriores deste lote ainda não concluídas. "
                "Registre a saída delas antes de dar entrada nesta etapa"
            )
        saida_anterior = (
            db.query(func.max(EtapaLote.data_saida))
            .filter(EtapaLote.lote_id == etapa.lote_id)
            .filter(EtapaLote.ordem < etapa.ordem)
            .scalar()
        )
        if saida_anterior and ocorrida_em < saida_anterior:
            raise _conflito(
                "A entrada não pode ser anterior à saída da etapa anterior"
            )
        if (
            lote.peso_total_kg is not None
            and total_entradas + dados.quantidade_kg
            > lote.peso_total_kg + EPS
        ):
            raise _conflito(
                "A soma das entradas ultrapassa o peso total do lote "
                f"({lote.peso_total_kg} kg)"
            )

    elif tipo == TipoMovimentacao.SAIDA:
        if etapa.data_entrada is None:
            raise _conflito("Registre uma entrada antes de registrar a saída")
        if ocorrida_em < etapa.data_entrada:
            raise _conflito("A saída não pode ser anterior à entrada")
        if dados.quantidade_kg > total_entradas + EPS:
            raise _conflito(
                f"A saída ({dados.quantidade_kg} kg) é maior que o total "
                f"que entrou na etapa ({total_entradas} kg)"
            )

    movimentacao = MovimentacaoEtapa(
        etapa_id=etapa.id,
        tipo=tipo,
        ocorrida_em=ocorrida_em,
        quantidade_kg=dados.quantidade_kg,
        responsavel=dados.responsavel,
        documento_referencia=dados.documento_referencia,
        observacao=dados.observacao,
        registrado_por_id=usuario_atual.id,
    )
    db.add(movimentacao)

    # Atualiza a etapa a partir do evento
    if tipo == TipoMovimentacao.ENTRADA:
        if etapa.data_entrada is None or ocorrida_em < etapa.data_entrada:
            etapa.data_entrada = ocorrida_em
        etapa.status = StatusEtapa.EM_ANDAMENTO
        if dados.responsavel:
            etapa.responsavel = dados.responsavel
    elif tipo == TipoMovimentacao.SAIDA:
        etapa.data_saida = ocorrida_em
        etapa.status = StatusEtapa.CONCLUIDA
    elif tipo == TipoMovimentacao.TRANSFERENCIA_RESPONSAVEL:
        etapa.responsavel = dados.responsavel

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflito(
            "Os dados informados violam as regras de integridade da etapa"
        )
    db.refresh(movimentacao)

    registrar_log(
        db,
        acao=TipoAcao.CRIAR,
        entidade="MovimentacaoEtapa",
        usuario_id=usuario_atual.id,
        entidade_id=movimentacao.id,
        detalhes=(
            f"Movimentação {tipo.value} registrada na etapa "
            f"{etapa.tipo.value} (ordem {etapa.ordem}) do lote "
            f"{lote.codigo_lote}"
            + (f", {dados.quantidade_kg} kg" if dados.quantidade_kg else "")
        ),
    )
    return _para_saida(movimentacao, usuario_atual.nome)


@router.get(
    "/etapas/{etapa_id}/movimentacoes",
    response_model=list[MovimentacaoOut],
)
def listar_movimentacoes(
    etapa_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Histórico da etapa, em ordem cronológica."""
    etapa = db.query(EtapaLote.id).filter(EtapaLote.id == etapa_id).first()
    if not etapa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa não encontrada",
        )
    linhas = (
        db.query(MovimentacaoEtapa, Usuario.nome)
        .outerjoin(Usuario, Usuario.id == MovimentacaoEtapa.registrado_por_id)
        .filter(MovimentacaoEtapa.etapa_id == etapa_id)
        .order_by(MovimentacaoEtapa.ocorrida_em, MovimentacaoEtapa.criado_em)
        .all()
    )
    return [_para_saida(m, nome) for m, nome in linhas]