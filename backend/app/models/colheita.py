import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.database import Base


class Colheita(Base):
    """
    Registro de um evento de colheita/coleta: quando e onde a produção
    de um talhão (numa safra específica) foi colhida, e a quantidade.
    """
    __tablename__ = "colheitas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Ponto exato onde a colheita foi registrada (pode ser diferente do
    # centro do talhão, já que a colheita pode ser registrada de qualquer
    # ponto dentro da área plantada).
    localizacao_coleta = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    data_colheita = Column(DateTime(timezone=True), nullable=False)
    quantidade_kg = Column(Float, nullable=False)

    talhao_safra_id = Column(UUID(as_uuid=True), ForeignKey("talhao_safra.id"), nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    talhao_safra = relationship("TalhaoSafra")

    def __repr__(self):
        return f"<Colheita {self.quantidade_kg}kg em {self.data_colheita}>"