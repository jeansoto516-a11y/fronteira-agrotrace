import uuid
import enum 
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, Date, Enum, UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import column_property
from geoalchemy2 import Geometry, Geography

from app.db.database import Base

class TipoAreaRestrita(str, enum.Enum):
    EMBARGO =   "embargo"
    DESMATAMENTO = "desmatamento"

class AreaRestrita(Base):
    __tablename__ = "areas_restritas"
    __table_args__ = (
        UniqueConstraint("tipo", "identificador", name="uq_area_tipo_identificador"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(Enum(TipoAreaRestrita), nullable=False)
    identificador = Column(String(100), nullable=False)  # ex: "EMB-SIM-0001"
    descricao = Column(String(500), nullable=True)
    fonte = Column(
        String(150), nullable=False,
        default="SIMULADO", server_default="SIMULADO",
    )
    data_referencia = Column(Date, nullable=False)

    geometria = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False
    )
    area_calculada_m2 = column_property(
        func.ST_Area(func.cast(geometria, Geography))
    )

    criado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<AreaRestrita {self.tipo} {self.identificador}>"