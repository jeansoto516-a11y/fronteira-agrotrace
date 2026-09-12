import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Produtor(Base):
    """
    Produtor rural — dono de uma ou mais fazendas.
    Pode ou não ter um Usuario vinculado (login no sistema).
    """
    __tablename__ = "produtores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(150), nullable=False)
    cpf_cnpj = Column(String(18), unique=True, nullable=False, index=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Um produtor pode ter várias fazendas (relacionamento 1:N)
    fazendas = relationship("Fazenda", back_populates="produtor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Produtor {self.nome} ({self.cpf_cnpj})>"