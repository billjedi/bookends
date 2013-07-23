"""Move from 'excited' to 'exciting'

Revision ID: 1436b8136d84
Revises: None
Create Date: 2013-07-22 22:50:50.342937

"""

# revision identifiers, used by Alembic.
revision = '1436b8136d84'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('book', 'excited', new_column_name='exciting')

def downgrade():
    op.alter_column('book', 'exciting', new_column_name='excited')
