import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.etapa_lote import TipoEtapa, StatusEtapa, ModalTransporte

CAMPOS_TRANSPORTE = (
    "modal", "placa_veiculo", "transportadora", "origem", "destino",
)
CAMPOS_EXPORTACAO = ("pais_destino", "importador", "navio")

OBRIGATORIOS_POR_TIPO = {
    TipoEtapa.ARMAZEM: ("local_nome", "estado"),
    TipoEtapa.TRANSPORTE: ("modal", "origem", "destino"),
    TipoEtapa.PORTO: ("local_nome", "estado"),
    TipoEtapa.EXPORTACAO: ("pais_destino", "importador"),
}


def validar_regras_do_tipo(tipo: TipoEtapa, dados: dict) -> list[str]:
    """
    Regras de preenchimento por tipo de etapa. Devolve a lista de erros
    (vazia = tudo certo). Usada no cadastro (aqui) e na edição (router),
    onde os dados são o resultado da mistura do que já existia com o
    que foi enviado.
    """
    if tipo == TipoEtapa.FAZENDA:
        return [
            "A etapa 'fazenda' é montada automaticamente pela "
            "rastreabilidade e não pode ser cadastrada"
        ]

    erros = []
    for campo in OBRIGATORIOS_POR_TIPO[tipo]:
        if dados.get(campo) in (None, ""):
            erros.append(
                f"O campo '{campo}' é obrigatório para etapas do "
                f"tipo '{tipo.value}'"
            )
    if tipo != TipoEtapa.TRANSPORTE:
        for campo in CAMPOS_TRANSPORTE:
            if dados.get(campo) not in (None, ""):
                erros.append(
                    f"O campo '{campo}' só se aplica a etapas de transporte"
                )
    if tipo != TipoEtapa.EXPORTACAO:
        for campo in CAMPOS_EXPORTACAO:
            if dados.get(campo) not in (None, ""):
                erros.append(
                    f"O campo '{campo}' só se aplica a etapas de exportação"
                )
    return erros


class _CamposCadastrais(BaseModel):
    """Campos descritivos da etapa, comuns ao cadastro e à edição."""
    model_config = {"extra": "forbid"}

    local_nome: Optional[str] = Field(None, max_length=150)
    municipio: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    documento_referencia: Optional[str] = Field(None, max_length=100)
    observacoes: Optional[str] = Field(None, max_length=1000)
    modal: Optional[ModalTransporte] = None
    placa_veiculo: Optional[str] = Field(None, max_length=20)
    transportadora: Optional[str] = Field(None, max_length=150)
    origem: Optional[str] = Field(None, max_length=150)
    destino: Optional[str] = Field(None, max_length=150)
    pais_destino: Optional[str] = Field(None, max_length=100)
    importador: Optional[str] = Field(None, max_length=150)
    navio: Optional[str] = Field(None, max_length=150)

    @field_validator(
        "local_nome", "municipio", "documento_referencia", "observacoes",
        "placa_veiculo", "transportadora", "origem", "destino",
        "pais_destino", "importador", "navio",
        mode="before",
    )
    @classmethod
    def _limpar_texto(cls, valor):
        if isinstance(valor, str):
            valor = valor.strip()
            return valor or None
        return valor

    @field_validator("placa_veiculo")
    @classmethod
    def _placa_maiuscula(cls, valor):
        return valor.upper() if valor else valor

    @field_validator("estado", mode="before")
    @classmethod
    def _validar_uf(cls, valor):
        if valor is None:
            return None
        valor = str(valor).strip().upper()
        if not valor:
            return None
        if len(valor) != 2 or not valor.isalpha():
            raise ValueError("O estado deve ser a sigla da UF, com 2 letras")
        return valor

    @model_validator(mode="after")
    def _coordenadas_juntas(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Informe latitude e longitude juntas")
        return self


class EtapaLoteCreate(_CamposCadastrais):
    """
    Cadastro de uma etapa. A ordem é automática, o status começa como
    'planejada' e as datas vêm das movimentações: por isso esses campos
    não existem aqui (enviá-los gera erro).
    """
    tipo: TipoEtapa
    responsavel: Optional[str] = Field(None, max_length=150)

    @field_validator("responsavel", mode="before")
    @classmethod
    def _limpar_responsavel(cls, valor):
        if isinstance(valor, str):
            valor = valor.strip()
            return valor or None
        return valor

    @model_validator(mode="after")
    def _regras_do_tipo(self):
        erros = validar_regras_do_tipo(self.tipo, self.model_dump())
        if erros:
            raise ValueError("; ".join(erros))
        return self


class EtapaLoteUpdate(_CamposCadastrais):
    """
    Correção dos dados cadastrais. Responsável, status e datas mudam
    apenas por movimentação, então não são aceitos aqui.
    """


class EtapaLoteOut(BaseModel):
    id: uuid.UUID
    lote_id: uuid.UUID
    tipo: TipoEtapa
    ordem: int
    status: StatusEtapa
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
    criado_em: Optional[datetime] = None

    model_config = {"from_attributes": True}