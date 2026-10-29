import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum, Boolean, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class TipoNotificacao(str, enum.Enum):
    DOCUMENTO_VENCENDO = "documento_vencendo"
    SOBREPOSICAO_AREA = "sobreposicao_area"
    ETAPA_PENDENTE = "etapa_pendente"


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(Enum(TipoNotificacao), nullable=False, index=True)
    mensagem = Column(String(300), nullable=False)
    # Página do frontend para onde a notificação leva (ex: "/documentos").
    link = Column(String(200), nullable=False)
    # Identifica o evento que gerou a notificação (ex: "etapa_pendente:<lote_id>").
    # É única: a rotina roda todo dia e nunca cria a mesma notificação duas vezes.
    chave = Column(String(200), nullable=False, unique=True)
    lido = Column(
        Boolean, nullable=False, default=False,
        server_default=text("false"),
    )
    criado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Notificacao {self.tipo} chave={self.chave}>"