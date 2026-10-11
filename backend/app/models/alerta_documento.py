import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey,
    Boolean, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class TipoAlerta(str, enum.Enum):
    VENCE_30_DIAS = "vence_30_dias"
    VENCE_15_DIAS = "vence_15_dias"
    VENCE_7_DIAS = "vence_7_dias"
    VENCIDO = "vencido"


class AlertaDocumento(Base):
    __tablename__ = "alertas_documento"
    __table_args__ = (
        # Garante que o mesmo documento nunca gere o mesmo tipo de
        # alerta duas vezes (a rotina roda todo dia).
        UniqueConstraint(
            "documento_id", "tipo_alerta",
            name="uq_alerta_documento_tipo",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_alerta = Column(Enum(TipoAlerta), nullable=False)
    mensagem = Column(String(300), nullable=False)
    lido = Column(
        Boolean, nullable=False, default=False,
        server_default=text("false"),
    )
    criado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<AlertaDocumento {self.tipo_alerta} doc={self.documento_id}>"