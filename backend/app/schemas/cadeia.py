import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.etapa_lote import TipoEtapa, StatusEtapa, ModalTransporte


class OrigemFazendaCadeia(BaseModel):
    """Uma fazenda de origem do lote (só na etapa automática 'fazenda')."""
    fazenda_id: uuid.UUID
    fazenda_nome: str
    municipio: str
    estado: str
    produtor_nome: str
    quantidade_kg: float


class EtapaCadeiaOut(BaseModel):
    id: Optional[uuid.UUID] = None
    tipo: TipoEtapa
    ordem: int
    status: StatusEtapa
    automatica: bool
    local_nome: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    data_entrada: Optional[datetime] = None
    data_saida: Optional[datetime] = None
    responsavel: Optional[str] = None
    documento_referencia: Optional[str] = None
    observacoes: Optional[str] = None
    modal: Optional[ModalTransporte] = None
    placa_veiculo: Optional[str] = None
    transportadora: Optional[str] = None
    origem: Optional[str] = None
    destino: Optional[str] = None
    pais_destino: Optional[str] = None
    importador: Optional[str] = None
    navio: Optional[str] = None
    origens: Optional[list[OrigemFazendaCadeia]] = None


class LinhaDoTempoLoteOut(BaseModel):
    lote_id: uuid.UUID
    codigo_lote: str
    peso_total_kg: Optional[float] = None
    etapas: list[EtapaCadeiaOut]
    etapas_pendentes: list[TipoEtapa]