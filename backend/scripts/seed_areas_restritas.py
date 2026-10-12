from datetime import date

from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from shapely.geometry import MultiPolygon, box

import app.models  # noqa: F401 — registra todas as models
from app.db.database import SessionLocal
from app.models.talhao import Talhao
from app.models.area_restrita import AreaRestrita, TipoAreaRestrita


def _wkt_multi(*poligonos) -> WKTElement:
    """Monta um MULTIPOLYGON (SRID 4326) a partir de polígonos shapely."""
    return WKTElement(MultiPolygon(list(poligonos)).wkt, srid=4326)


def main():
    db = SessionLocal()
    try:
        talhao = db.query(Talhao).order_by(Talhao.criado_em).first()
        if talhao is None:
            print("Nenhum talhão cadastrado: cadastre um talhão e rode de novo.")
            return

        minx, miny, maxx, maxy = to_shape(talhao.poligono).bounds
        w = maxx - minx
        h = maxy - miny
        print(f"Usando como referência o talhão: {talhao.nome_identificador}")

        areas = [
            # Sobrepõem o talhão de referência (casos "com interseção")
            dict(
                tipo=TipoAreaRestrita.EMBARGO,
                identificador="EMB-SIM-0001",
                descricao="Embargo simulado sobre o canto nordeste do talhão de referência",
                data_referencia=date(2025, 3, 14),
                geom=_wkt_multi(
                    box(minx + w * 0.6, miny + h * 0.6, maxx + w * 0.4, maxy + h * 0.4)
                ),
            ),
            dict(
                tipo=TipoAreaRestrita.DESMATAMENTO,
                identificador="DESM-SIM-0001",
                descricao="Alerta de desmatamento simulado sobre o canto sudoeste do talhão de referência",
                data_referencia=date(2024, 8, 2),
                geom=_wkt_multi(
                    box(minx - w * 0.3, miny - h * 0.3, minx + w * 0.25, miny + h * 0.25)
                ),
            ),
            # Distantes do talhão (casos "sem interseção")
            dict(
                tipo=TipoAreaRestrita.EMBARGO,
                identificador="EMB-SIM-0002",
                descricao="Embargo simulado distante do talhão de referência",
                data_referencia=date(2023, 11, 20),
                geom=_wkt_multi(
                    box(minx + 0.40, miny + 0.30, minx + 0.43, miny + 0.33)
                ),
            ),
            dict(
                tipo=TipoAreaRestrita.DESMATAMENTO,
                identificador="DESM-SIM-0002",
                descricao="Desmatamento simulado com duas manchas, distante do talhão de referência",
                data_referencia=date(2025, 1, 9),
                geom=_wkt_multi(
                    box(minx - 0.35, miny - 0.30, minx - 0.33, miny - 0.28),
                    box(minx - 0.31, miny - 0.27, minx - 0.29, miny - 0.25),
                ),
            ),
            dict(
                tipo=TipoAreaRestrita.EMBARGO,
                identificador="EMB-SIM-0003",
                descricao="Embargo simulado distante do talhão de referência",
                data_referencia=date(2022, 6, 5),
                geom=_wkt_multi(
                    box(minx + 0.10, miny - 0.45, minx + 0.14, miny - 0.41)
                ),
            ),
        ]

        criadas = 0
        for item in areas:
            existe = (
                db.query(AreaRestrita)
                .filter(AreaRestrita.tipo == item["tipo"])
                .filter(AreaRestrita.identificador == item["identificador"])
                .first()
            )
            if existe:
                continue
            db.add(
                AreaRestrita(
                    tipo=item["tipo"],
                    identificador=item["identificador"],
                    descricao=item["descricao"],
                    data_referencia=item["data_referencia"],
                    fonte="SIMULADO",
                    geometria=item["geom"],
                )
            )
            criadas += 1

        db.commit()
        print(f"Áreas criadas: {criadas} (já existiam: {len(areas) - criadas})")
    finally:
        db.close()


if __name__ == "__main__":
    main()