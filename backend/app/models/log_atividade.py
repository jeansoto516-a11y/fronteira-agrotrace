import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class TipoAcao(str, enum.Enum):
    """Tipos de ação que podem ser registrados na auditoria."""
    CRIAR = "criar"
    EDITAR = "editar"
    EXCLUIR = "excluir"
    LOGIN = "login"
    LOGIN_FALHOU = "login_falhou"


class LogAtividade(Base):
    """
    Registro de auditoria: quem fez o quê, quando, e em qual entidade.
    Genérico para todas as entidades do sistema (Produtor, Fazenda,
    Talhão, Lote, etc), identificadas por nome + ID.
    """
    __tablename__ = "logs_atividade"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    acao = Column(Enum(TipoAcao), nullable=False)

    # Nome da entidade afetada (ex: "Produtor", "Fazenda", "Talhao")
    entidade = Column(String(50), nullable=False)
    entidade_id = Column(UUID(as_uuid=True), nullable=True)

    # Descrição livre e legível do que aconteceu (ex: "Produtor João Silva cadastrado")
    detalhes = Column(String(500), nullable=True)

    ip_origem = Column(String(45), nullable=True)  # suporta IPv4 e IPv6
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    usuario = relationship("Usuario")

    def __repr__(self):
        return f"<LogAtividade {self.acao} em {self.entidade} por {self.usuario_id}>"