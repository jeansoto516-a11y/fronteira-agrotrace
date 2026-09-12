import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class TalhaoSafra(Base):
    """
    Tabela de vínculo: representa "este Talhão, nesta Safra, plantou
    esta Cultura". Um talhão pode aparecer em várias safras diferentes,
    cada vez com uma cultura (ex: soja na safra de verão, milho na safrinha).
    """
    __tablename__ = "talhao_safra"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talhao_id = Column(UUID(as_uuid=True), ForeignKey("talhoes.id"), nullable=False)
    safra_id = Column(UUID(as_uuid=True), ForeignKey("safras.id"), nullable=False)
    cultura_id = Column(UUID(as_uuid=True), ForeignKey("culturas.id"), nullable=False)

    talhao = relationship("Talhao")
    safra = relationship("Safra")
    cultura = relationship("Cultura")

    def __repr__(self):
        return f"<TalhaoSafra talhao={self.talhao_id} safra={self.safra_id}>"