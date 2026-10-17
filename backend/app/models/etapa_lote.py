import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Enum, ForeignKey,
    UniqueConstraint, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


def _agora():
    return datetime.now(timezone.utc)


class TipoEtapa(str, enum.Enum):
    FAZENDA = "fazenda"
    ARMAZEM = "armazem"
    TRANSPORTE = "transporte"
    PORTO = "porto"
    EXPORTACAO = "exportacao"


class StatusEtapa(str, enum.Enum):
    PLANEJADA = "planejada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"


class ModalTransporte(str, enum.Enum):
    RODOVIARIO = "rodoviario"
    FERROVIARIO = "ferroviario"
    HIDROVIARIO = "hidroviario"


class EtapaLote(Base):
    """
    Etapa da cadeia por onde um lote passa depois de colhido:
    armazém → transporte → porto → exportação.
    A etapa 'fazenda' (origem) não é digitada: ela é montada a partir
    da rastreabilidade (Lote → LoteColheita → Colheita → Talhão → Fazenda).
    Os campos específicos de cada tipo são opcionais; a API vai validar
    quais são obrigatórios para cada tipo.
    """
    __tablename__ = "etapas_lote"
    __table_args__ = (
        UniqueConstraint("lote_id", "ordem", name="uq_etapa_lote_ordem"),
        CheckConstraint("ordem > 0", name="ck_etapa_ordem_positiva"),
        CheckConstraint(
            "data_entrada IS NULL OR data_saida IS NULL "
            "OR data_saida >= data_entrada",
            name="ck_etapa_datas",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lotes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Campos comuns a todas as etapas
    tipo = Column(Enum(TipoEtapa), nullable=False)
    ordem = Column(Integer, nullable=False)
    status = Column(
        Enum(StatusEtapa),
        nullable=False,
        default=StatusEtapa.PLANEJADA,
        server_default=StatusEtapa.PLANEJADA.name,
    )
    local_nome = Column(String(150), nullable=True)
    municipio = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    data_entrada = Column(DateTime(timezone=True), nullable=True)
    data_saida = Column(DateTime(timezone=True), nullable=True)
    responsavel = Column(String(150), nullable=True)
    documento_referencia = Column(String(100), nullable=True)
    observacoes = Column(String(1000), nullable=True)

    # Específicos de TRANSPORTE
    modal = Column(Enum(ModalTransporte), nullable=True)
    placa_veiculo = Column(String(20), nullable=True)
    transportadora = Column(String(150), nullable=True)
    origem = Column(String(150), nullable=True)
    destino = Column(String(150), nullable=True)

    # Específicos de EXPORTACAO
    pais_destino = Column(String(100), nullable=True)
    importador = Column(String(150), nullable=True)
    navio = Column(String(150), nullable=True)

    criado_em = Column(DateTime(timezone=True), default=_agora)

    def __repr__(self):
        return f"<EtapaLote lote={self.lote_id} {self.tipo} #{self.ordem}>"