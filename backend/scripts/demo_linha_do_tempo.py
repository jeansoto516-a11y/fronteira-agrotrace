import sys
from datetime import datetime, timedelta, timezone

import app.models  # noqa: F401 — registra todas as models
from app.db.database import SessionLocal
from app.core.cadeia import montar_linha_do_tempo
from app.models.lote import Lote
from app.models.etapa_lote import (
    EtapaLote, TipoEtapa, StatusEtapa, ModalTransporte,
)

MARCA_DEMO = "DEMO"


def _imprimir(linha: dict) -> None:
    print(f"\nLote {linha['codigo_lote']} ({linha['peso_total_kg']} kg)")
    print("-" * 60)
    for e in linha["etapas"]:
        local = e.get("local_nome") or "-"
        uf = f"/{e['estado']}" if e.get("estado") else ""
        auto = " [automática]" if e["automatica"] else ""
        print(f"{e['ordem']}. {e['tipo'].upper()} ({e['status']}){auto}")
        print(f"   local: {local}{uf}")
        print(f"   entrada: {e.get('data_entrada')} | saída: {e.get('data_saida')}")
        if e["tipo"] == "fazenda":
            for o in e["origens"]:
                print(
                    f"   origem: {o['fazenda_nome']} ({o['produtor_nome']}) "
                    f"- {o['quantidade_kg']} kg"
                )
        if e["tipo"] == "transporte":
            print(
                f"   {e['modal']} | {e['origem']} → {e['destino']} | "
                f"placa {e['placa_veiculo']}"
            )
    print("-" * 60)
    print(f"Etapas ainda não registradas: {linha['etapas_pendentes']}")


def main():
    limpar = len(sys.argv) > 1 and sys.argv[1] == "limpar"
    db = SessionLocal()
    try:
        lote = db.query(Lote).order_by(Lote.criado_em).first()
        if lote is None:
            print("Nenhum lote cadastrado. Crie um lote (POST /lotes/) e rode de novo.")
            return

        if limpar:
            apagadas = (
                db.query(EtapaLote)
                .filter(EtapaLote.lote_id == lote.id)
                .filter(EtapaLote.observacoes == MARCA_DEMO)
                .delete()
            )
            db.commit()
            print(f"Etapas de demonstração removidas: {apagadas}")
            return

        ja_existem = (
            db.query(EtapaLote).filter(EtapaLote.lote_id == lote.id).count()
        )
        if ja_existem == 0:
            agora = datetime.now(timezone.utc)
            db.add_all(
                [
                    EtapaLote(
                        lote_id=lote.id, tipo=TipoEtapa.ARMAZEM, ordem=1,
                        status=StatusEtapa.CONCLUIDA,
                        local_nome="Armazém Demo", municipio="Sorriso", estado="MT",
                        data_entrada=agora - timedelta(days=10),
                        data_saida=agora - timedelta(days=8),
                        responsavel="Armazéns Demo Ltda",
                        documento_referencia="NF-DEMO-001",
                        observacoes=MARCA_DEMO,
                    ),
                    EtapaLote(
                        lote_id=lote.id, tipo=TipoEtapa.TRANSPORTE, ordem=2,
                        status=StatusEtapa.EM_ANDAMENTO,
                        modal=ModalTransporte.RODOVIARIO,
                        origem="Sorriso/MT", destino="Santos/SP",
                        placa_veiculo="ABC1D23",
                        transportadora="Transportadora Demo",
                        data_saida=agora - timedelta(days=8),
                        documento_referencia="CTE-DEMO-001",
                        observacoes=MARCA_DEMO,
                    ),
                    EtapaLote(
                        lote_id=lote.id, tipo=TipoEtapa.PORTO, ordem=3,
                        status=StatusEtapa.PLANEJADA,
                        local_nome="Porto de Santos", municipio="Santos", estado="SP",
                        observacoes=MARCA_DEMO,
                    ),
                ]
            )
            db.commit()
            print("Etapas de demonstração criadas.")
        else:
            print(f"O lote já tem {ja_existem} etapa(s): nada foi criado.")

        _imprimir(montar_linha_do_tempo(db, lote.id))
    finally:
        db.close()


if __name__ == "__main__":
    main()