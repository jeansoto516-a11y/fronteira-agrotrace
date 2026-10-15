import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.area_restrita import TipoAreaRestrita


class SinalizacaoOut(BaseModel):
    id: uuid.UUID
    talhao_id: uuid.UUID
    talhao_nome: str
    fazenda_id: uuid.UUID
    area_restrita_id: uuid.UUID
    tipo: TipoAreaRestrita
    identificador: str
    descricao: Optional[str] = None
    fonte: str
    data_referencia: date
    area_sobreposta_hectares: float
    percentual_do_talhao: float
    ativa: bool
    detectada_em: Optional[datetime] = None
    atualizada_em: Optional[datetime] = None
    resolvida_em: Optional[datetime] = None


class ResumoSinalizacoesOut(BaseModel):
    talhoes_sinalizados: int
    sinalizacoes_ativas: int
    embargos: int
    desmatamentos: int


class SincronizacaoOut(BaseModel):
    criadas: int
    atualizadas: int
    reativadas: int
    resolvidas: int