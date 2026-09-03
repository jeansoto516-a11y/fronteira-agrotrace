import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class PerfilUsuario(str, enum.Enum):
    """
    Perfis de acesso do sistema (Tarefa: Perfis de acesso).
    Cada perfil enxerga e faz coisas diferentes na plataforma.
    """
    PRODUTOR = "produtor"
    COOPERATIVA_ADMIN = "cooperativa_admin"
    AUDITOR_COMPLIANCE = "auditor_compliance"
    EXPORTADOR = "exportador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilUsuario), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Usuario {self.email} ({self.perfil})>"