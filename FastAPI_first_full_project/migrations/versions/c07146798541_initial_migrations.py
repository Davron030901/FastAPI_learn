"""initial migrations

Revision ID: c07146798541
Revises: 
Create Date: 2024-12-25 18:34:57.720697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c07146798541'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('band',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('genre', sa.Enum('ROCK', 'ELECTRONIK', 'METAL', 'HIP_HOP', name='genrechoises'), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date_formed', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('album',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('release_date', sa.Date(), nullable=False),
    sa.Column('band_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['band_id'], ['band.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('album')
    op.drop_table('band')
    # ### end Alembic commands ###
