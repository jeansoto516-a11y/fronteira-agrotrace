import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.database import Base


class Fazenda(Base):
    """
    Fazenda pertencente a um Produtor. Tem uma localização central
    (ponto) e é subdividida em Talhões (que têm seus próprios polígonos).
    """
    __tablename__ = "fazendas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(150), nullable=False)
    municipio = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)  # ex: "MT", "BA"
    area_total_hectares = Column(Float, nullable=True)

    # Ponto central da fazenda (latitude/longitude), útil para exibir
    # no mapa antes mesmo de detalhar os talhões individualmente.
    # SRID 4326 = sistema de coordenadas GPS padrão (WGS 84).
    localizacao = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    produtor_id = Column(UUID(as_uuid=True), ForeignKey("produtores.id"), nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    produtor = relationship("Produtor", back_populates="fazendas")
    talhoes = relationship("Talhao", back_populates="fazenda", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fazenda {self.nome} - {self.municipio}/{self.estado}>"