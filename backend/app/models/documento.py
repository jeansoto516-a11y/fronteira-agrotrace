import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, Date, Enum,
    ForeignKey, Integer, Boolean, text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class TipoDocumento(str, enum.Enum):
    CAR = "car"
    LICENCA_AMBIENTAL = "licenca_ambiental"
    LAUDO_TECNICO = "laudo_tecnico"
    OUTRO = "outro"


class EntidadeDocumento(str, enum.Enum):
    FAZENDA = "fazenda"
    TALHAO = "talhao"


class Documento(Base):
    __tablename__ = "documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grupo_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    versao = Column(Integer, nullable=False, default=1, server_default="1")
    vigente = Column(
        Boolean, nullable=False, default=True,
        server_default=text("true"),
    )
    tipo = Column(Enum(TipoDocumento), nullable=False)
    entidade_tipo = Column(Enum(EntidadeDocumento), nullable=False)
    entidade_id = Column(UUID(as_uuid=True), nullable=False)
    nome_arquivo_original = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(500), nullable=False)
    data_validade = Column(Date, nullable=True)
    enviado_por_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    criado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Documento {self.tipo} v{self.versao}>"