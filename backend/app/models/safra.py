import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Safra(Base):
    """
    Safra: ciclo de produção de um determinado ano/período
    (ex: "Safra 2025/2026"). Compartilhada entre vários talhões.
    """
    __tablename__ = "safras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identificacao = Column(String(30), unique=True, nullable=False)  # ex: "2025/2026"
    ano_inicio = Column(Integer, nullable=False)
    ano_fim = Column(Integer, nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Safra {self.identificacao}>"