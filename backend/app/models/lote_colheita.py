import uuid

from sqlalchemy import Column, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class LoteColheita(Base):
    """
    Tabela de vínculo: representa "este Lote contém X kg desta Colheita".
    É a peça-chave da rastreabilidade reversa: a partir de um Lote,
    seguimos até a(s) Colheita(s) → Talhão(ões) → Fazenda(s) de origem.
    """
    __tablename__ = "lote_colheita"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=False)
    colheita_id = Column(UUID(as_uuid=True), ForeignKey("colheitas.id"), nullable=False)
    quantidade_kg = Column(Float, nullable=False)  # quanto dessa colheita foi para este lote

    lote = relationship("Lote", back_populates="colheitas_vinculadas")
    colheita = relationship("Colheita")

    def __repr__(self):
        return f"<LoteColheita lote={self.lote_id} colheita={self.colheita_id}>"