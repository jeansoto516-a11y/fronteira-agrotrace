import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, DateTime, Enum, ForeignKey,
    Index, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


def _agora():
    return datetime.now(timezone.utc)


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    TRANSFERENCIA_RESPONSAVEL = "transferencia_responsavel"
    OCORRENCIA = "ocorrencia"


class MovimentacaoEtapa(Base):
    """
    Evento ocorrido em uma etapa da cadeia (entrada, saída, troca de
    responsável ou ocorrência). É o histórico de auditoria: não se edita
    nem se apaga. Correções são feitas com uma nova movimentação.
    'registrado_por_id' é o usuário do sistema que lançou o evento;
    'responsavel' é quem tem a custódia do lote na etapa (pessoa/empresa).
    """
    __tablename__ = "movimentacoes_etapa"
    __table_args__ = (
        CheckConstraint(
            "quantidade_kg IS NULL OR quantidade_kg > 0",
            name="ck_movimentacao_quantidade_positiva",
        ),
        Index(
            "ix_movimentacoes_etapa_ocorrida",
            "etapa_id", "ocorrida_em",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    etapa_id = Column(
        UUID(as_uuid=True),
        ForeignKey("etapas_lote.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    ocorrida_em = Column(DateTime(timezone=True), nullable=False)
    quantidade_kg = Column(Float, nullable=True)
    responsavel = Column(String(150), nullable=True)
    documento_referencia = Column(String(100), nullable=True)
    observacao = Column(String(1000), nullable=True)
    registrado_por_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    criado_em = Column(DateTime(timezone=True), default=_agora)

    def __repr__(self):
        return f"<MovimentacaoEtapa etapa={self.etapa_id} {self.tipo}>"