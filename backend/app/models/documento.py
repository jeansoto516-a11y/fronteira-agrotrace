import uuid
import enum
from datetime import datetime, timezone, date

from sqlalchemy import Column, String, DateTime, Date, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class TipoDocumento(str, enum.Enum):
    """Tipos de documento de certificação socioambiental aceitos."""
    CAR = "car"  # Cadastro Ambiental Rural
    LICENCA_AMBIENTAL = "licenca_ambiental"
    LAUDO_TECNICO = "laudo_tecnico"
    OUTRO = "outro"


class EntidadeDocumento(str, enum.Enum):
    """A qual tipo de entidade o documento está vinculado."""
    FAZENDA = "fazenda"
    TALHAO = "talhao"


class Documento(Base):
    """
    Documento de certificação socioambiental (CAR, licença, laudo),
    vinculado a uma Fazenda ou a um Talhão. O arquivo em si fica
    salvo em disco local; aqui guardamos só o caminho e os metadados.
    """
    __tablename__ = "documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(Enum(TipoDocumento), nullable=False)

    # Vínculo polimórfico simples: guarda o tipo de entidade e o ID dela,
    # em vez de duas foreign keys opcionais (fazenda_id/talhao_id).
    entidade_tipo = Column(Enum(EntidadeDocumento), nullable=False)
    entidade_id = Column(UUID(as_uuid=True), nullable=False)

    nome_arquivo_original = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(500), nullable=False)  # caminho no disco local
    data_validade = Column(Date, nullable=True)  # algumas licenças expiram; outras não

    enviado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Documento {self.tipo} - {self.nome_arquivo_original}>"