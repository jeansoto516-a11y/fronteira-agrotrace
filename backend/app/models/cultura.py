import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Cultura(Base):
    """
    Tipo de cultura agrícola (ex: Soja, Café). Cadastro simples,
    reutilizado em várias safras ao longo do tempo.
    """
    __tablename__ = "culturas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(80), unique=True, nullable=False)  # ex: "Soja", "Café Arábica"

    def __repr__(self):
        return f"<Cultura {self.nome}>"