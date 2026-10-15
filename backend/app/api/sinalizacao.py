import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_usuario_atual, exigir_perfil
from app.core.sinalizacao import sincronizar_sinalizacoes
from app.models.usuario import Usuario, PerfilUsuario
from app.models.talhao import Talhao
from app.models.area_restrita import AreaRestrita, TipoAreaRestrita
from app.models.sinalizacao_talhao import SinalizacaoTalhao
from app.schemas.sinalizacao import (
    SinalizacaoOut,
    ResumoSinalizacoesOut,
    SincronizacaoOut,
)

router = APIRouter(prefix="/sinalizacoes", tags=["Sinalizações"])

ADMIN = PerfilUsuario.COOPERATIVA_ADMIN


def _consulta(db: Session):
    """Sinalização + dados do talhão e da área (sem carregar geometrias)."""
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
        )
        .join(Talhao, Talhao.id == SinalizacaoTalhao.talhao_id)
        .join(
            AreaRestrita,
            AreaRestrita.id == SinalizacaoTalhao.area_restrita_id,
        )
    )


def _para_saida(linha) -> SinalizacaoOut:
    s, nome, fazenda_id, tipo, identificador, descricao, fonte, data_ref = linha
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
    )


@router.get("/", response_model=list[SinalizacaoOut])
def listar_sinalizacoes(
    apenas_ativas: bool = True,
    tipo: TipoAreaRestrita | None = None,
    talhao_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    """Lista as sinalizações de talhões. Use apenas_ativas=false p/ histórico."""
    consulta = _consulta(db)
    if apenas_ativas:
        consulta = consulta.filter(SinalizacaoTalhao.ativa.is_(True))
    if tipo:
        consulta = consulta.filter(AreaRestrita.tipo == tipo)
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


@router.post("/sincronizar", response_model=SincronizacaoOut)
def sincronizar_agora(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(exigir_perfil(ADMIN)),
):
    """Dispara a verificação manualmente (a rotina diária faz o mesmo)."""
    return sincronizar_sinalizacoes(db)