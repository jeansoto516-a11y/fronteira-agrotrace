import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.movimentacao_etapa import TipoMovimentacao

# Data sem fuso horário é interpretada como horário de Brasília.
FUSO_PADRAO = ZoneInfo("America/Sao_Paulo")
TOLERANCIA_FUTURO = timedelta(minutes=5)


class MovimentacaoCreate(BaseModel):
    """
    Registro de um evento em uma etapa. Se 'ocorrida_em' não for
    informada, o router usa o momento atual.
    """
    model_config = {"extra": "forbid"}

    tipo: TipoMovimentacao
    ocorrida_em: Optional[datetime] = None
    quantidade_kg: Optional[float] = Field(None, gt=0)
    responsavel: Optional[str] = Field(None, max_length=150)
    documento_referencia: Optional[str] = Field(None, max_length=100)
    observacao: Optional[str] = Field(None, max_length=1000)

    @field_validator(
        "responsavel", "documento_referencia", "observacao", mode="before"
    )
    @classmethod
    def _limpar_texto(cls, valor):
        if isinstance(valor, str):
            valor = valor.strip()
            return valor or None
        return valor

    @field_validator("ocorrida_em")
    @classmethod
    def _validar_data(cls, valor):
        if valor is None:
            return None
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=FUSO_PADRAO)
        if valor > datetime.now(timezone.utc) + TOLERANCIA_FUTURO:
            raise ValueError("A data da movimentação não pode estar no futuro")
        return valor.astimezone(timezone.utc)

    @model_validator(mode="after")
    def _regras_do_tipo(self):
        if (
            self.tipo in (TipoMovimentacao.ENTRADA, TipoMovimentacao.SAIDA)
            and self.quantidade_kg is None
        ):
            raise ValueError(
                "Informe a quantidade em kg para entrada e saída"
            )
        if (
            self.tipo == TipoMovimentacao.TRANSFERENCIA_RESPONSAVEL
            and not self.responsavel
        ):
            raise ValueError(
                "Informe o novo responsável na transferência de responsável"
            )
        if self.tipo == TipoMovimentacao.OCORRENCIA and (
            not self.observacao or len(self.observacao) < 5
        ):
            raise ValueError(
                "Descreva a ocorrência (mínimo de 5 caracteres)"
            )
        return self


class MovimentacaoOut(BaseModel):
    id: uuid.UUID
    etapa_id: uuid.UUID
    tipo: TipoMovimentacao
    ocorrida_em: datetime
    quantidade_kg: Optional[float] = None
    responsavel: Optional[str] = None
    documento_referencia: Optional[str] = None
    observacao: Optional[str] = None
    registrado_por_id: Optional[uuid.UUID] = None
    registrado_por_nome: Optional[str] = None
    criado_em: Optional[datetime] = None