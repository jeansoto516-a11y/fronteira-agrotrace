from datetime import date, timedelta

import app.models  # noqa: F401 — registra todas as models
from app.db.database import SessionLocal
from app.core.conformidade import avaliar_todos


def _imprimir(titulo: str, avaliacoes: list[dict]) -> None:
    print(f"\n=== {titulo} ===")
    if not avaliacoes:
        print("Nenhum lote cadastrado.")
        return
    for a in avaliacoes:
        print(
            f"\nLote {a['codigo_lote']}: {a['status'].value.upper()} "
            f"({a['total_impeditivos']} impeditivo(s), "
            f"{a['total_avisos']} aviso(s); "
            f"{a['total_fazendas']} fazenda(s), {a['total_talhoes']} talhão(ões))"
        )
        for m in a["motivos"]:
            print(f"  - [{m['severidade'].value}] {m['detalhe']}")


def main():
    db = SessionLocal()
    try:
        hoje = date.today()
        _imprimir(f"Situação de hoje ({hoje})", avaliar_todos(db, hoje))

        # Simulação: a mesma base, um ano e meio no futuro. Serve para ver
        # o status 'vencido' sem alterar nenhum dado.
        futuro = hoje + timedelta(days=548)
        _imprimir(
            f"SIMULAÇÃO em {futuro} (nada é gravado)",
            avaliar_todos(db, futuro),
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()