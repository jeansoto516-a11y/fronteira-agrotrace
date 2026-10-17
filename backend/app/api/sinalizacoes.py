import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.sinalizacao import sincronizar_sinalizacoes
from app.core.auditoria import registrar_log
from app.models.log_atividade import TipoAcao
from app.models.usuario import Usuario, PerfilUsuario
from app.models.talhao import Talhao
from app.models.area_restrita import AreaRestrita, TipoAreaRestrita
from app.models.sinalizacao_talhao import SinalizacaoTalhao, StatusRevisao
from app.schemas.sinalizacao import (
    SinalizacaoOut,
    ResumoSinalizacoesOut,
    SincronizacaoOut,
    RevisaoIn,
)

router = APIRouter(prefix="/sinalizacoes", tags=["Sinalizações"])

ADMIN = PerfilUsuario.COOPERATIVA_ADMIN
AUDITOR = PerfilUsuario.AUDITOR_COMPLIANCE


def _consulta(db: Session):
    """Sinalização + dados do talhão, da área e do revisor (sem geometrias)."""
    return (
        db.query(
            SinalizacaoTalhao,
            Talhao.nome_identificador,
            Talhao.fazenda_id,
            AreaRestrita.tipo,
            AreaRestrita.identificador,
            AreaRestrita.descricao,
            AreaRestrita.fonte,
            AreaRestrita.data_referencia,
            Usuario.nome,
        )
        .select_from(SinalizacaoTalhao)
        .join(Talhao, Talhao.id == SinalizacaoTalhao.talhao_id)
        .join(
            AreaRestrita,
            AreaRestrita.id == SinalizacaoTalhao.area_restrita_id,
        )
        .outerjoin(Usuario, Usuario.id == SinalizacaoTalhao.revisado_por_id)
    )


def _para_saida(linha) -> SinalizacaoOut:
    (
        s, nome, fazenda_id, tipo, identificador,
        descricao, fonte, data_ref, revisor_nome,
    ) = linha
    return SinalizacaoOut(
        id=s.id,
        talhao_id=s.talhao_id,
        talhao_nome=nome,
        fazenda_id=fazenda_id,
        area_restrita_id=s.area_restrita_id,
        tipo=tipo,
        identificador=identificador,
        descricao=descricao,
        fonte=fonte,
        data_referencia=data_ref,
        area_sobreposta_hectares=s.area_sobreposta_hectares,
        percentual_do_talhao=s.percentual_do_talhao,
        ativa=s.ativa,
        detectada_em=s.detectada_em,
        atualizada_em=s.atualizada_em,
        resolvida_em=s.resolvida_em,
        status_revisao=s.status_revisao,
        parecer=s.parecer,
        revisado_por_id=s.revisado_por_id,
        revisado_por_nome=revisor_nome,
        revisado_em=s.revisado_em,
    )


@router.get("/", response_model=list[SinalizacaoOut])
def listar_sinalizacoes(
    apenas_ativas: bool = True,
    tipo: TipoAreaRestrita | None = None,
    status_revisao: StatusRevisao | None = None,
    talhao_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Lista as sinalizações. Use apenas_ativas=false p/ incluir o histórico."""
    consulta = _consulta(db)
    if apenas_ativas:
        consulta = consulta.filter(SinalizacaoTalhao.ativa.is_(True))
    if tipo:
        consulta = consulta.filter(AreaRestrita.tipo == tipo)
    if status_revisao:
        consulta = consulta.filter(
            SinalizacaoTalhao.status_revisao == status_revisao
        )
    if talhao_id:
        consulta = consulta.filter(SinalizacaoTalhao.talhao_id == talhao_id)
    linhas = (
        consulta.order_by(SinalizacaoTalhao.detectada_em.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_para_saida(l) for l in linhas]


@router.get("/resumo", response_model=ResumoSinalizacoesOut)
def resumo_sinalizacoes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Contadores das sinalizações ativas (para o dashboard)."""
    ativa = SinalizacaoTalhao.ativa.is_(True)

    total = db.query(func.count(SinalizacaoTalhao.id)).filter(ativa).scalar()
    talhoes = (
        db.query(func.count(func.distinct(SinalizacaoTalhao.talhao_id)))
        .filter(ativa)
        .scalar()
    )
    pendentes = (
        db.query(func.count(SinalizacaoTalhao.id))
        .filter(ativa)
        .filter(SinalizacaoTalhao.status_revisao == StatusRevisao.PENDENTE)
        .scalar()
    )
    por_tipo = dict(
        db.query(AreaRestrita.tipo, func.count(SinalizacaoTalhao.id))
        .select_from(SinalizacaoTalhao)
        .join(
            AreaRestrita,
            AreaRestrita.id == SinalizacaoTalhao.area_restrita_id,
        )
        .filter(ativa)
        .group_by(AreaRestrita.tipo)
        .all()
    )
    return ResumoSinalizacoesOut(
        talhoes_sinalizados=talhoes or 0,
        sinalizacoes_ativas=total or 0,
        embargos=por_tipo.get(TipoAreaRestrita.EMBARGO, 0),
        desmatamentos=por_tipo.get(TipoAreaRestrita.DESMATAMENTO, 0),
        pendentes_revisao=pendentes or 0,
    )


@router.get("/talhoes/{talhao_id}", response_model=list[SinalizacaoOut])
def sinalizacoes_do_talhao(
    talhao_id: uuid.UUID,
    incluir_historico: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Sinalizações de um talhão (lista vazia = talhão sem restrição)."""
    consulta = _consulta(db).filter(SinalizacaoTalhao.talhao_id == talhao_id)
    if not incluir_historico:
        consulta = consulta.filter(SinalizacaoTalhao.ativa.is_(True))
    linhas = consulta.order_by(SinalizacaoTalhao.detectada_em.desc()).all()
    return [_para_saida(l) for l in linhas]


@router.patch("/{sinalizacao_id}/revisao", response_model=SinalizacaoOut)
def revisar_sinalizacao(
    sinalizacao_id: uuid.UUID,
    dados: RevisaoIn,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(AUDITOR)),
):
    """Revisão manual pelo auditor de compliance (confirmar ou descartar)."""
    sinalizacao = (
        db.query(SinalizacaoTalhao)
        .filter(SinalizacaoTalhao.id == sinalizacao_id)
        .first()
    )
    if not sinalizacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sinalização não encontrada",
        )
    if not sinalizacao.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sinalização já resolvida: a sobreposição não existe mais",
        )

    novo_status = (
        StatusRevisao.CONFIRMADA
        if dados.decisao == "confirmada"
        else StatusRevisao.DESCARTADA
    )
    sinalizacao.status_revisao = novo_status
    sinalizacao.parecer = dados.parecer
    sinalizacao.revisado_por_id = usuario_atual.id
    sinalizacao.revisado_em = datetime.now(timezone.utc)
    db.commit()

    registrar_log(
        db,
        acao=TipoAcao.EDITAR,
        entidade="SinalizacaoTalhao",
        usuario_id=usuario_atual.id,
        entidade_id=sinalizacao.id,
        detalhes=f"Sinalização revisada como {novo_status.value}"
        + (f": {dados.parecer}" if dados.parecer else ""),
    )

    linha = _consulta(db).filter(SinalizacaoTalhao.id == sinalizacao_id).first()
    return _para_saida(linha)


@router.post("/sincronizar", response_model=SincronizacaoOut)
def sincronizar_agora(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    """Dispara a verificação manualmente (a rotina diária faz o mesmo)."""
    return sincronizar_sinalizacoes(db)