from datetime import date

from pydantic import BaseModel


class VolumePorStatusOut(BaseModel):
    completo_kg: float
    pendente_kg: float
    vencido_kg: float


class VolumeRastreadoOut(BaseModel):
    total_kg: float
    por_status: VolumePorStatusOut


class LotesCertificadosOut(BaseModel):
    total_lotes: int
    certificados: int
    percentual: float


class AlertasIndicadorOut(BaseModel):
    documentos_em_alerta: int
    vencidos: int
    vencem_7_dias: int
    vencem_15_dias: int
    vencem_30_dias: int
    nao_lidos: int


class IndicadoresOut(BaseModel):
    gerado_em: date
    volume_rastreado: VolumeRastreadoOut
    lotes_certificados: LotesCertificadosOut
    alertas: AlertasIndicadorOut