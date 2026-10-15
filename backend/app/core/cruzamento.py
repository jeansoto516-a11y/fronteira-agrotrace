import uuid

from geoalchemy2 import Geography
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.talhao import Talhao
from app.models.area_restrita import AreaRestrita


def _consultar_interseccoes(db: Session, talhao_id: uuid.UUID | None = None):
    """
    Cruza talhões com áreas restritas usando ST_Intersects e calcula
    a área da sobreposição (ST_Intersection) em metros quadrados.
    Cada linha retornada = (Talhao, AreaRestrita, sobreposicao_m2).
    """
    # 'geography' devolve metros quadrados reais (mesmo padrão das
    # áreas calculadas nos models Talhao e AreaRestrita).
    sobreposicao_m2 = func.ST_Area(
        func.cast(
            func.ST_Intersection(Talhao.poligono, AreaRestrita.geometria),
            Geography,
        )
    )

    consulta = (
        db.query(Talhao, AreaRestrita, sobreposicao_m2.label("sobreposicao_m2"))
        .select_from(Talhao)
        .join(
            AreaRestrita,
            func.ST_Intersects(Talhao.poligono, AreaRestrita.geometria),
        )
    )
    if talhao_id is not None:
        consulta = consulta.filter(Talhao.id == talhao_id)

    return consulta.order_by(
        Talhao.nome_identificador, AreaRestrita.data_referencia.desc()
    ).all()


def _montar_resultado(talhao: Talhao, itens: list) -> dict:
    """Monta o dicionário de saída de um talhão. 'itens' = [(area, m2)]."""
    area_talhao_m2 = talhao.area_calculada_m2 or 0

    interseccoes = []
    for area, m2 in itens:
        m2 = m2 or 0
        percentual = (m2 / area_talhao_m2 * 100) if area_talhao_m2 else 0.0
        interseccoes.append(
            {
                "area_id": area.id,
                "tipo": area.tipo,
                "identificador": area.identificador,
                "descricao": area.descricao,
                "fonte": area.fonte,
                "data_referencia": area.data_referencia,
                "area_sobreposta_hectares": round(m2 / 10_000, 4),
                "percentual_do_talhao": round(percentual, 2),
            }
        )

    return {
        "talhao_id": talhao.id,
        "nome_identificador": talhao.nome_identificador,
        "fazenda_id": talhao.fazenda_id,
        "area_talhao_hectares": round(area_talhao_m2 / 10_000, 4),
        "possui_restricao": len(interseccoes) > 0,
        "interseccoes": interseccoes,
    }


def cruzar_talhao(db: Session, talhao: Talhao) -> dict:
    """Cruzamento de um único talhão com a base de áreas restritas."""
    linhas = _consultar_interseccoes(db, talhao.id)
    return _montar_resultado(talhao, [(area, m2) for _, area, m2 in linhas])


def cruzar_todos(db: Session) -> list[dict]:
    """Cruzamento de todos os talhões (inclui os sem nenhuma restrição)."""
    por_talhao: dict[uuid.UUID, list] = {}
    for talhao, area, m2 in _consultar_interseccoes(db):
        por_talhao.setdefault(talhao.id, []).append((area, m2))

    talhoes = db.query(Talhao).order_by(Talhao.nome_identificador).all()
    return [_montar_resultado(t, por_talhao.get(t.id, [])) for t in talhoes]