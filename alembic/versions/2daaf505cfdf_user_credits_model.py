"""user credits model

Revision ID: 2daaf505cfdf
Revises: 3b8967108418
Create Date: 2024-07-07 11:13:45.307963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2daaf505cfdf'
down_revision: Union[str, None] = '3b8967108418'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('credits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('credits', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credits_id'), 'credits', ['id'], unique=False)
    op.create_index(op.f('ix_credits_user_id'), 'credits', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_credits_user_id'), table_name='credits')
    op.drop_index(op.f('ix_credits_id'), table_name='credits')
    op.drop_table('credits')
    # ### end Alembic commands ###
