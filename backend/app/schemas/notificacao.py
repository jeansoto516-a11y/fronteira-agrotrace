import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.notificacao import TipoNotificacao


class NotificacaoOut(BaseModel):
    id: uuid.UUID
    tipo: TipoNotificacao
    mensagem: str
    link: str
    lido: bool
    criado_em: Optional[datetime] = None


class ResumoNotificacoesOut(BaseModel):
    nao_lidos: int
    documentos_vencendo: int
    sobreposicoes_area: int
    etapas_pendentes: int