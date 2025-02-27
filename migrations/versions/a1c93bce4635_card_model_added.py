"""Card model added

Revision ID: a1c93bce4635
Revises: 1a9852da17a5
Create Date: 2024-10-08 17:31:39.695751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c93bce4635'
down_revision = '1a9852da17a5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('account', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=10), server_default='Active', nullable=True))

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=10), server_default='Active', nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('is_active')

    with op.batch_alter_table('account', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
