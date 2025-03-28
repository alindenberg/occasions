"""Add is_processing column to occasion table

Revision ID: 5b68c2bf2a70
Revises: d5497d27cfa8
Create Date: 2024-10-23 09:30:07.485939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b68c2bf2a70'
down_revision: Union[str, None] = 'd5497d27cfa8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('occasions', sa.Column('is_processing', sa.Boolean(), server_default=sa.sql.false(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('occasions', 'is_processing')
    # ### end Alembic commands ###
