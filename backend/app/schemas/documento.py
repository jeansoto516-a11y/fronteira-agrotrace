import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel

from app.models.documento import TipoDocumento, EntidadeDocumento


class DocumentoOut(BaseModel):
    """O que a API devolve ao consultar um documento."""
    id: uuid.UUID
    tipo: TipoDocumento
    entidade_tipo: EntidadeDocumento
    entidade_id: uuid.UUID
    nome_arquivo_original: str
    data_validade: Optional[date] = None
    enviado_por_id: uuid.UUID
    criado_em: datetime

    model_config = {"from_attributes": True}