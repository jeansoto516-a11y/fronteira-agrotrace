import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.core.conformidade import StatusConformidade, TipoMotivo, Severidade


class MotivoConformidadeOut(BaseModel):
    tipo: TipoMotivo
    severidade: Severidade
    entidade_tipo: str
    entidade_id: uuid.UUID
    entidade_nome: str
    documento_tipo: Optional[str] = None
    data_validade: Optional[date] = None
    detalhe: str


class ConformidadeLoteOut(BaseModel):
    lote_id: uuid.UUID
    codigo_lote: str
    peso_total_kg: Optional[float] = None
    status: StatusConformidade
    avaliado_em: date
    total_fazendas: int
    total_talhoes: int
    total_impeditivos: int
    total_avisos: int
    motivos: list[MotivoConformidadeOut]


class ResumoConformidadeOut(BaseModel):
    total_lotes: int
    completos: int
    pendentes: int
    vencidos: int
    com_avisos: int