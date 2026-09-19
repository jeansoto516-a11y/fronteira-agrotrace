import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from sqlalchemy import func
from sqlalchemy.orm import column_property
from geoalchemy2 import Geography

from app.db.database import Base


class Talhao(Base):
    """
    Talhão: menor unidade de produção dentro de uma Fazenda.
    Representado por um polígono geoespacial (a área plantada real),
    usado depois para cruzamento com áreas de desmatamento/embargo.
    """
    __tablename__ = "talhoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_identificador = Column(String(100), nullable=False)  # ex: "Talhão 03"
    area_hectares = Column(Float, nullable=True)

    # Polígono geoespacial da área do talhão (o dado mais crítico do projeto).
    # SRID 4326, igual ao usado na Fazenda, para manter consistência.
    poligono = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    # Área calculada automaticamente pelo PostGIS a partir do polígono,
    # convertendo para 'geography' para o cálculo considerar a curvatura
    # da Terra e retornar metros quadrados corretos (não graus).
    area_calculada_m2 = column_property(
        func.ST_Area(func.cast(poligono, Geography))
    )
    

    fazenda_id = Column(UUID(as_uuid=True), ForeignKey("fazendas.id"), nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    fazenda = relationship("Fazenda", back_populates="talhoes")

    # Vínculos que ainda vamos criar nas próximas tarefas do cronograma:
    # safras_vinculadas = relationship("TalhaoSafra", back_populates="talhao")
    # colheitas = relationship("Colheita", back_populates="talhao")

    def __repr__(self):
        return f"<Talhao {self.nome_identificador} - {self.area_hectares}ha>"