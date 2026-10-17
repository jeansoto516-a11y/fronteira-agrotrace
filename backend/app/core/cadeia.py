import uuid

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.models.etapa_lote import EtapaLote, TipoEtapa

# Etapas que alguém precisa registrar. A de origem (fazenda) é montada
# automaticamente pela rastreabilidade do lote.
ETAPAS_REGISTRAVEIS = [
    TipoEtapa.ARMAZEM,
    TipoEtapa.TRANSPORTE,
    TipoEtapa.PORTO,
    TipoEtapa.EXPORTACAO,
]


def _etapa_origem(lote: Lote) -> dict:
    """
    Monta a etapa 'fazenda' a partir da rastreabilidade:
    Lote → LoteColheita → Colheita → Talhão → Fazenda → Produtor.
    Um lote pode vir de várias fazendas; as quantidades são somadas.
    """
    por_fazenda: dict = {}
    datas = []
    for vinculo in lote.colheitas_vinculadas:
        colheita = vinculo.colheita
        fazenda = colheita.talhao_safra.talhao.fazenda
        produtor = fazenda.produtor
        item = por_fazenda.setdefault(
            fazenda.id,
            {
                "fazenda_id": fazenda.id,
                "fazenda_nome": fazenda.nome,
                "municipio": fazenda.municipio,
                "estado": fazenda.estado,
                "produtor_nome": produtor.nome,
                "quantidade_kg": 0.0,
            },
        )
        item["quantidade_kg"] += vinculo.quantidade_kg
        datas.append(colheita.data_colheita)

    origens = sorted(por_fazenda.values(), key=lambda o: o["fazenda_nome"])

    if len(origens) == 1:
        local_nome = origens[0]["fazenda_nome"]
        municipio = origens[0]["municipio"]
        estado = origens[0]["estado"]
    else:
        local_nome = f"{len(origens)} fazendas de origem"
        municipio = None
        estado = None

    return {
        "id": None,
        "tipo": TipoEtapa.FAZENDA.value,
        "ordem": 0,
        "status": "concluida",
        "automatica": True,
        "local_nome": local_nome,
        "municipio": municipio,
        "estado": estado,
        "data_entrada": min(datas) if datas else None,
        "data_saida": max(datas) if datas else None,
        "origens": origens,
    }


def _etapa_registrada(e: EtapaLote) -> dict:
    return {
        "id": e.id,
        "tipo": e.tipo.value,
        "ordem": e.ordem,
        "status": e.status.value,
        "automatica": False,
        "local_nome": e.local_nome,
        "municipio": e.municipio,
        "estado": e.estado,
        "latitude": e.latitude,
        "longitude": e.longitude,
        "data_entrada": e.data_entrada,
        "data_saida": e.data_saida,
        "responsavel": e.responsavel,
        "documento_referencia": e.documento_referencia,
        "observacoes": e.observacoes,
        "modal": e.modal.value if e.modal else None,
        "placa_veiculo": e.placa_veiculo,
        "transportadora": e.transportadora,
        "origem": e.origem,
        "destino": e.destino,
        "pais_destino": e.pais_destino,
        "importador": e.importador,
        "navio": e.navio,
    }


def montar_linha_do_tempo(db: Session, lote_id: uuid.UUID) -> dict | None:
    """
    Linha do tempo completa de um lote: origem (automática) seguida das
    etapas registradas, em ordem. Devolve None se o lote não existir.
    'etapas_pendentes' lista os tipos que ainda não foram registrados.
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if lote is None:
        return None

    registradas = (
        db.query(EtapaLote)
        .filter(EtapaLote.lote_id == lote.id)
        .order_by(EtapaLote.ordem)
        .all()
    )
    tipos_registrados = {e.tipo for e in registradas}

    return {
        "lote_id": lote.id,
        "codigo_lote": lote.codigo_lote,
        "peso_total_kg": lote.peso_total_kg,
        "etapas": [_etapa_origem(lote)]
        + [_etapa_registrada(e) for e in registradas],
        "etapas_pendentes": [
            t.value for t in ETAPAS_REGISTRAVEIS if t not in tipos_registrados
        ],
    }