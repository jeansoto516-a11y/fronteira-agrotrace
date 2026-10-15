import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Float, Boolean, DateTime, ForeignKey,
    UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


def _agora():
    return datetime.now(timezone.utc)


class SinalizacaoTalhao(Base):
    """
    Sinalização de que um talhão se sobrepõe a uma área restrita
    (embargo ou desmatamento). Quando a sobreposição deixa de existir,
    a linha não é apagada: fica ativa=False com 'resolvida_em'.
    """
    __tablename__ = "sinalizacoes_talhao"
    __table_args__ = (
        UniqueConstraint(
            "talhao_id", "area_restrita_id",
            name="uq_sinalizacao_talhao_area",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talhao_id = Column(
        UUID(as_uuid=True),
        ForeignKey("talhoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    area_restrita_id = Column(
        UUID(as_uuid=True),
        ForeignKey("areas_restritas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    area_sobreposta_hectares = Column(Float, nullable=False)
    percentual_do_talhao = Column(Float, nullable=False)
    ativa = Column(
        Boolean, nullable=False, default=True,
        server_default=text("true"),
    )
    detectada_em = Column(DateTime(timezone=True), default=_agora)
    atualizada_em = Column(DateTime(timezone=True), default=_agora)
    resolvida_em = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return (
            f"<SinalizacaoTalhao talhao={self.talhao_id} "
            f"area={self.area_restrita_id} ativa={self.ativa}>"
        )