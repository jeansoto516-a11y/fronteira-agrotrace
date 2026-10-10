"""versionamento documentos

Revision ID: c2dabce2f46a
Revises: a38f4c3eabad
Create Date: 2026-10-09 22:03:00.059882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2dabce2f46a'
down_revision: Union[str, Sequence[str], None] = 'a38f4c3eabad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'documentos',
        sa.Column('grupo_id', sa.UUID(), nullable=True),
    )
    op.add_column(
        'documentos',
        sa.Column('versao', sa.Integer(),
        server_default='1', nullable=False),
    )
    op.add_column(
        'documentos',
        sa.Column('vigente', sa.Boolean(),
        server_default=sa.text('true'), nullable=False),
    )
    op.execute('UPDATE documentos SET grupo_id = id')
    op.alter_column('documentos', 'grupo_id', nullable=False)
    op.create_index(
        op.f('ix_documentos_grupo_id'),
        'documentos', ['grupo_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_documentos_grupo_id'), table_name='documentos',
    )
    op.drop_column('documentos', 'vigente')
    op.drop_column('documentos', 'versao')
    op.drop_column('documentos', 'grupo_id')