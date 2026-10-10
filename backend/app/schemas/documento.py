import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, computed_field

from app.models.documento import TipoDocumento, EntidadeDocumento


class DocumentoOut(BaseModel):
    id: uuid.UUID
    grupo_id: uuid.UUID
    versao: int
    vigente: bool
    tipo: TipoDocumento
    entidade_tipo: EntidadeDocumento
    entidade_id: uuid.UUID
    nome_arquivo_original: str
    data_validade: Optional[date] = None
    enviado_por_id: uuid.UUID
    criado_em: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def dias_para_vencer(self) -> Optional[int]:
        if self.data_validade is None:
            return None
        return (self.data_validade - date.today()).days

    @computed_field
    @property
    def situacao_validade(self) -> str:
        dias = self.dias_para_vencer
        if dias is None:
            return "sem_validade"
        if dias < 0:
            return "vencido"
        if dias <= 30:
            return "a_vencer"
        return "valido"