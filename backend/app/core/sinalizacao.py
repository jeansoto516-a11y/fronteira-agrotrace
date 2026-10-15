import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.cruzamento import _consultar_interseccoes
from app.models.sinalizacao_talhao import SinalizacaoTalhao

# Sobreposição mínima (em m²) para sinalizar. Talhão que apenas encosta
# na borda de uma área restrita tem sobreposição 0 e NÃO é sinalizado.
SOBREPOSICAO_MINIMA_M2 = 1.0


def sincronizar_sinalizacoes(
    db: Session, talhao_id: uuid.UUID | None = None
) -> dict:
    """
    Compara as sobreposições reais de hoje (talhão x área restrita) com
    as sinalizações gravadas e deixa o banco em dia:
      - cria a sinalização de quem passou a se sobrepor;
      - atualiza hectares/percentual se o valor mudou;
      - reativa uma sinalização antiga que voltou a se sobrepor;
      - resolve (ativa=False) a que deixou de se sobrepor.
    Se talhao_id for informado, só esse talhão é verificado.
    Pode rodar quantas vezes quiser: sem mudança, não altera nada.
    """
    agora = datetime.now(timezone.utc)

    # 1) Sobreposições reais hoje: {(talhao_id, area_id): (hectares, %)}
    atuais: dict[tuple, tuple] = {}
    for talhao, area, m2 in _consultar_interseccoes(db, talhao_id):
        m2 = m2 or 0
        if m2 < SOBREPOSICAO_MINIMA_M2:
            continue
        area_talhao_m2 = talhao.area_calculada_m2 or 0
        percentual = (m2 / area_talhao_m2 * 100) if area_talhao_m2 else 0.0
        atuais[(talhao.id, area.id)] = (
            round(m2 / 10_000, 4),
            round(percentual, 2),
        )

    # 2) Sinalizações já gravadas (ativas ou não)
    consulta = db.query(SinalizacaoTalhao)
    if talhao_id is not None:
        consulta = consulta.filter(SinalizacaoTalhao.talhao_id == talhao_id)
    existentes = {
        (s.talhao_id, s.area_restrita_id): s for s in consulta.all()
    }

    criadas = atualizadas = reativadas = resolvidas = 0

    # 3) Cria, reativa ou atualiza
    for chave, (hectares, percentual) in atuais.items():
        sinalizacao = existentes.get(chave)
        if sinalizacao is None:
            db.add(
                SinalizacaoTalhao(
                    talhao_id=chave[0],
                    area_restrita_id=chave[1],
                    area_sobreposta_hectares=hectares,
                    percentual_do_talhao=percentual,
                )
            )
            criadas += 1
        elif not sinalizacao.ativa:
            sinalizacao.ativa = True
            sinalizacao.resolvida_em = None
            sinalizacao.detectada_em = agora
            sinalizacao.area_sobreposta_hectares = hectares
            sinalizacao.percentual_do_talhao = percentual
            sinalizacao.atualizada_em = agora
            reativadas += 1
        elif (
            sinalizacao.area_sobreposta_hectares != hectares
            or sinalizacao.percentual_do_talhao != percentual
        ):
            sinalizacao.area_sobreposta_hectares = hectares
            sinalizacao.percentual_do_talhao = percentual
            sinalizacao.atualizada_em = agora
            atualizadas += 1

    # 4) Resolve o que deixou de se sobrepor
    for chave, sinalizacao in existentes.items():
        if sinalizacao.ativa and chave not in atuais:
            sinalizacao.ativa = False
            sinalizacao.resolvida_em = agora
            sinalizacao.atualizada_em = agora
            resolvidas += 1

    if criadas or atualizadas or reativadas or resolvidas:
        db.commit()

    return {
        "criadas": criadas,
        "atualizadas": atualizadas,
        "reativadas": reativadas,
        "resolvidas": resolvidas,
    }



def sincronizar_sinalizacoes_seguro(
    db: Session, talhao_id: uuid.UUID
) -> None:
    """
    Versão usada dentro das rotas da API: se der algum erro na
    sincronização, registra no terminal e segue em frente, para não
    derrubar o cadastro/edição do talhão.
    """
    try:
        sincronizar_sinalizacoes(db, talhao_id)
    except Exception as e:
        db.rollback()
        print(f"[sinalizacao] ERRO ao sincronizar talhão {talhao_id}: {e}")