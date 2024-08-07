"""stripe customer model

Revision ID: d415a6e70b63
Revises: 2daaf505cfdf
Create Date: 2024-07-10 20:02:17.461850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd415a6e70b63'
down_revision: Union[str, None] = '2daaf505cfdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('stripe_customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('stripe_customer_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stripe_customer_id')
    )
    op.create_index(op.f('ix_stripe_customers_id'), 'stripe_customers', ['id'], unique=False)
    op.create_index(op.f('ix_stripe_customers_user_id'), 'stripe_customers', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_stripe_customers_user_id'), table_name='stripe_customers')
    op.drop_index(op.f('ix_stripe_customers_id'), table_name='stripe_customers')
    op.drop_table('stripe_customers')
    # ### end Alembic commands ###
