import uuid
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel

from app.models.alerta_documento import TipoAlerta
from app.models.documento import TipoDocumento, EntidadeDocumento


class AlertaDocumentoOut(BaseModel):
    id: uuid.UUID
    documento_id: uuid.UUID
    tipo_alerta: TipoAlerta
    mensagem: str
    lido: bool
    criado_em: Optional[datetime] = None
    documento_tipo: TipoDocumento
    entidade_tipo: EntidadeDocumento
    entidade_id: uuid.UUID
    data_validade: Optional[date] = None