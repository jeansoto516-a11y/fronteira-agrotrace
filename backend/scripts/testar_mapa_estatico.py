import os
import sys
import time

import app.models  # noqa: F401 — registra todas as models
from app.core.config import settings
from app.core.mapa_estatico import obter_mapa_base
from app.core.relatorio import coletar_dados_relatorio
from app.db.database import SessionLocal
from app.models.lote import Lote
from app.models.usuario import Usuario


def main():
    codigo = sys.argv[1] if len(sys.argv) > 1 else None
    db = SessionLocal()
    try:
        consulta = db.query(Lote)
        if codigo:
            lote = consulta.filter(Lote.codigo_lote == codigo).first()
        else:
            lote = consulta.order_by(Lote.criado_em).first()
        if lote is None:
            print("Lote não encontrado (ou nenhum lote cadastrado).")
            return

        usuario = db.query(Usuario).order_by(Usuario.criado_em).first()
        dados = coletar_dados_relatorio(db, lote.id, usuario)

        pontos = [p for tal in dados["talhoes"] for p in tal["coordenadas"]]
        pontos += [
            p
            for sin in dados["sinalizacoes"]
            for anel in sin["coordenadas"]
            for p in anel
        ]

        inicio = time.perf_counter()
        mapa = obter_mapa_base(pontos)
        segundos = time.perf_counter() - inicio

        if mapa is None:
            print("Sem mapa de fundo (veja a mensagem acima).")
            return

        os.makedirs(settings.PASTA_UPLOADS, exist_ok=True)
        caminho = os.path.join(settings.PASTA_UPLOADS, "teste_mapa_fundo.jpg")
        with open(caminho, "wb") as arquivo:
            arquivo.write(mapa["imagem"])
        print(
            f"Mapa de fundo gerado em {segundos:.1f} s | zoom {mapa['zoom']} | "
            f"{mapa['largura_px']}x{mapa['altura_px']} px | "
            f"{len(mapa['imagem']) // 1024} KB"
        )
        print(f"Arquivo: {caminho}")
    finally:
        db.close()


if __name__ == "__main__":
    main()