import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Lote(Base):
    """
    Lote: agrupamento de uma ou mais Colheitas, formado para fins de
    comercialização/exportação. Mantém rastreabilidade reversa até
    o(s) talhão(ões) de origem através da tabela LoteColheita.
    """
    __tablename__ = "lotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_lote = Column(String(50), unique=True, nullable=False)  # ex: "LOTE-2026-001"
    peso_total_kg = Column(Float, nullable=True)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    colheitas_vinculadas = relationship("LoteColheita", back_populates="lote", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lote {self.codigo_lote}>"