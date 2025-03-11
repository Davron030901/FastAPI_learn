"""add starting price to auto_plates

Revision ID: add_starting_price
Revises: previous_revision
Create Date: 2024-03-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric

# revision identifiers, used by Alembic.
revision = 'add_starting_price'
down_revision = None  # change this to your previous revision
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('auto_plates', sa.Column('starting_price', Numeric(10, 2), nullable=False, server_default='1000'))

def downgrade():
    op.drop_column('auto_plates', 'starting_price')