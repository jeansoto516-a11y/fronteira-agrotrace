import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, model_validator

from app.models.area_restrita import TipoAreaRestrita
from app.models.sinalizacao_talhao import StatusRevisao


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
    status_revisao: StatusRevisao
    parecer: Optional[str] = None
    revisado_por_id: Optional[uuid.UUID] = None
    revisado_por_nome: Optional[str] = None
    revisado_em: Optional[datetime] = None


class ResumoSinalizacoesOut(BaseModel):
    talhoes_sinalizados: int
    sinalizacoes_ativas: int
    embargos: int
    desmatamentos: int
    pendentes_revisao: int


class SincronizacaoOut(BaseModel):
    criadas: int
    atualizadas: int
    reativadas: int
    resolvidas: int


class RevisaoIn(BaseModel):
    """Decisão do auditor. Descartar exige parecer (mín. 10 caracteres)."""
    decisao: Literal["confirmada", "descartada"]
    parecer: Optional[str] = None

    @model_validator(mode="after")
    def validar_parecer(self):
        if self.parecer is not None:
            self.parecer = self.parecer.strip() or None
        if self.parecer is not None and len(self.parecer) > 1000:
            raise ValueError("O parecer pode ter no máximo 1000 caracteres")
        if self.decisao == "descartada" and (
            self.parecer is None or len(self.parecer) < 10
        ):
            raise ValueError(
                "Para descartar, informe um parecer com pelo menos 10 caracteres"
            )
        return self