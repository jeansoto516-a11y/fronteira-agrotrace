import sys
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.schemas.etapa import EtapaLoteCreate, EtapaLoteUpdate
from app.schemas.movimentacao import MovimentacaoCreate

falhas = 0


def verificar(descricao, esperado_ok, classe, dados):
    """Cria o schema com 'dados' e compara com o resultado esperado."""
    global falhas
    try:
        classe(**dados)
        passou, motivo = True, ""
    except ValidationError as e:
        passou, motivo = False, e.errors()[0]["msg"]
    certo = passou == esperado_ok
    if not certo:
        falhas += 1
    marca = "OK    " if certo else "FALHOU"
    detalhe = f" -> {motivo}" if not passou else ""
    print(f"[{marca}] {descricao}{detalhe}")


futuro = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

print("\n--- Etapas: devem ser aceitas ---")
verificar("armazém válido", True, EtapaLoteCreate,
            {"tipo": "armazem", "local_nome": "Armazém X", "estado": "mt"})
verificar("transporte válido", True, EtapaLoteCreate,
            {"tipo": "transporte", "modal": "rodoviario",
            "origem": "Sorriso/MT", "destino": "Santos/SP",
            "placa_veiculo": "abc1d23"})
verificar("porto válido", True, EtapaLoteCreate,
            {"tipo": "porto", "local_nome": "Porto de Santos", "estado": "SP"})
verificar("exportação válida", True, EtapaLoteCreate,
            {"tipo": "exportacao", "pais_destino": "China",
            "importador": "Importer Co."})
verificar("edição parcial válida", True, EtapaLoteUpdate,
            {"placa_veiculo": "xyz9k88"})

print("\n--- Etapas: devem ser recusadas ---")
verificar("tipo fazenda", False, EtapaLoteCreate,
            {"tipo": "fazenda", "local_nome": "Fazenda X", "estado": "MT"})
verificar("transporte sem modal", False, EtapaLoteCreate,
            {"tipo": "transporte", "origem": "A", "destino": "B"})
verificar("porto sem local", False, EtapaLoteCreate,
            {"tipo": "porto", "estado": "SP"})
verificar("exportação sem país", False, EtapaLoteCreate,
            {"tipo": "exportacao", "importador": "Importer Co."})
verificar("armazém com campo de transporte", False, EtapaLoteCreate,
            {"tipo": "armazem", "local_nome": "X", "estado": "MT",
            "modal": "rodoviario"})
verificar("transporte com campo de exportação", False, EtapaLoteCreate,
            {"tipo": "transporte", "modal": "rodoviario", "origem": "A",
            "destino": "B", "navio": "MSC Demo"})
verificar("estado por extenso", False, EtapaLoteCreate,
            {"tipo": "armazem", "local_nome": "X", "estado": "Mato Grosso"})
verificar("latitude sem longitude", False, EtapaLoteCreate,
            {"tipo": "armazem", "local_nome": "X", "estado": "MT",
            "latitude": -12.5})
verificar("status enviado no cadastro", False, EtapaLoteCreate,
            {"tipo": "armazem", "local_nome": "X", "estado": "MT",
            "status": "concluida"})
verificar("responsável enviado na edição", False, EtapaLoteUpdate,
            {"responsavel": "Fulano"})

print("\n--- Movimentações: devem ser aceitas ---")
verificar("entrada com quantidade", True, MovimentacaoCreate,
            {"tipo": "entrada", "quantidade_kg": 1000})
verificar("saída com data sem fuso", True, MovimentacaoCreate,
            {"tipo": "saida", "quantidade_kg": 950,
            "ocorrida_em": "2026-10-10T08:00:00"})
verificar("transferência com responsável", True, MovimentacaoCreate,
            {"tipo": "transferencia_responsavel", "responsavel": "Transp. Demo"})
verificar("ocorrência descrita", True, MovimentacaoCreate,
            {"tipo": "ocorrencia", "observacao": "Atraso por chuva"})

print("\n--- Movimentações: devem ser recusadas ---")
verificar("entrada sem quantidade", False, MovimentacaoCreate,
            {"tipo": "entrada"})
verificar("quantidade negativa", False, MovimentacaoCreate,
            {"tipo": "saida", "quantidade_kg": -5})
verificar("transferência sem responsável", False, MovimentacaoCreate,
            {"tipo": "transferencia_responsavel"})
verificar("ocorrência sem descrição", False, MovimentacaoCreate,
            {"tipo": "ocorrencia"})
verificar("data no futuro", False, MovimentacaoCreate,
            {"tipo": "entrada", "quantidade_kg": 10, "ocorrida_em": futuro})

print()
if falhas:
    print(f"{falhas} verificação(ões) FALHARAM.")
    sys.exit(1)
print("Todas as verificações passaram.")