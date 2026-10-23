import sys

import app.models  # noqa: F401 — registra todas as models
from app.db.database import SessionLocal
from app.core.relatorio import coletar_dados_relatorio
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
        d = coletar_dados_relatorio(db, lote.id, usuario)

        l = d["lote"]
        print(f"\nLote {l['codigo']} - {l['peso_total_kg']} kg")
        print(
            f"Gerado em {d['gerado_em']:%d/%m/%Y %H:%M} por "
            f"{d['gerado_por']['nome']} ({d['gerado_por']['perfil']})"
        )
        c = d["conformidade"]
        print(
            f"Conformidade: {c['status'].value.upper()} "
            f"({c['total_impeditivos']} impeditivo(s), "
            f"{c['total_avisos']} aviso(s))"
        )

        print(f"\nOrigens (colheitas): {len(d['origens'])}")
        for o in d["origens"]:
            print(
                f"  - {o['data_colheita']} | {o['quantidade_kg']} kg | "
                f"{o['safra']} / {o['cultura']} | {o['talhao_nome']} "
                f"({o['talhao_area_ha']} ha) | {o['fazenda_nome']}-{o['estado']} "
                f"| {o['produtor_nome']}"
            )

        print(f"\nFazendas: {len(d['fazendas'])}")
        for f in d["fazendas"]:
            print(f"  - {f['nome']} ({f['municipio']}/{f['estado']}): {f['quantidade_kg']} kg")

        print(f"\nTalhões: {len(d['talhoes'])}")
        for t in d["talhoes"]:
            print(
                f"  - {t['nome']} | {t['area_ha']} ha | centro "
                f"({t['latitude']}, {t['longitude']}) | "
                f"{len(t['coordenadas'])} vértices | {t['quantidade_kg']} kg"
            )

        print(f"\nDocumentos vigentes: {len(d['documentos'])}")
        for doc in d["documentos"]:
            print(
                f"  - {doc['entidade_tipo']} {doc['entidade_nome']}: "
                f"{doc['tipo']} v{doc['versao']} | validade "
                f"{doc['data_validade']} | {doc['situacao']}"
            )

        print(f"\nSinalizações ativas: {len(d['sinalizacoes'])}")
        for s in d["sinalizacoes"]:
            print(
                f"  - {s['talhao_nome']} x {s['area_identificador']} "
                f"({s['area_tipo']}) | {s['sobreposicao_ha']} ha | "
                f"{s['status_revisao']} | {len(s['coordenadas'])} polígono(s)"
            )

        print(f"\nCadeia de custódia: {len(d['cadeia']['etapas'])} etapa(s)")
        for e in d["cadeia"]["etapas"]:
            print(
                f"  - {e['ordem']}. {e['tipo']} ({e['status']}) | "
                f"{len(e['movimentacoes'])} movimentação(ões)"
            )
        print(f"  Pendentes: {d['cadeia']['etapas_pendentes']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()