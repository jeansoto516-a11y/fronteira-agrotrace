"""revisao manual das sinalizacoes

Revision ID: d2f1b776d185
Revises: 065dbbc08807
Create Date: 2026-10-16 20:57:33.169813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd2f1b776d185'
down_revision: Union[str, Sequence[str], None] = '065dbbc08807'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tipo criado/removido manualmente: o Alembic não cria Enum do PostgreSQL
# quando a coluna é adicionada a uma tabela já existente.
STATUS_REVISAO = postgresql.ENUM(
    'PENDENTE', 'CONFIRMADA', 'DESCARTADA',
    name='statusrevisao',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    STATUS_REVISAO.create(op.get_bind(), checkfirst=True)
    op.add_column('sinalizacoes_talhao', sa.Column('status_revisao', STATUS_REVISAO, server_default='PENDENTE', nullable=False))
    op.add_column('sinalizacoes_talhao', sa.Column('parecer', sa.String(length=1000), nullable=True))
    op.add_column('sinalizacoes_talhao', sa.Column('revisado_por_id', sa.UUID(), nullable=True))
    op.add_column('sinalizacoes_talhao', sa.Column('revisado_em', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key('fk_sinalizacoes_revisado_por', 'sinalizacoes_talhao', 'usuarios', ['revisado_por_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_sinalizacoes_revisado_por', 'sinalizacoes_talhao', type_='foreignkey')
    op.drop_column('sinalizacoes_talhao', 'revisado_em')
    op.drop_column('sinalizacoes_talhao', 'revisado_por_id')
    op.drop_column('sinalizacoes_talhao', 'parecer')
    op.drop_column('sinalizacoes_talhao', 'status_revisao')
    STATUS_REVISAO.drop(op.get_bind(), checkfirst=True)