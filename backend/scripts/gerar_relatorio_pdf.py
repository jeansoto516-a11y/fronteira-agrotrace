import os
import sys

import app.models  # noqa: F401 — registra todas as models
from app.core.config import settings
from app.core.relatorio import coletar_dados_relatorio
from app.core.relatorio_pdf import gerar_pdf_relatorio
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
        pdf = gerar_pdf_relatorio(dados)

        os.makedirs(settings.PASTA_UPLOADS, exist_ok=True)
        caminho = os.path.join(
            settings.PASTA_UPLOADS, f"relatorio-{lote.codigo_lote}.pdf"
        )
        with open(caminho, "wb") as arquivo:
            arquivo.write(pdf)
        print(f"Relatório gerado ({len(pdf)} bytes): {caminho}")
    finally:
        db.close()


if __name__ == "__main__":
    main()