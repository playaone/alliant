"""sender/receiver balance added to transaction model

Revision ID: eed62b868b8b
Revises: 
Create Date: 2024-10-08 09:05:51.467336

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'eed62b868b8b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('external_party', schema=None) as batch_op:
        batch_op.drop_index('email')
        batch_op.drop_index('phone')
        batch_op.drop_column('email')
        batch_op.drop_column('phone')

    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sender_balance', sa.Float(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('receiver_balance', sa.Float(), server_default='0', nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('receiver_balance')
        batch_op.drop_column('sender_balance')

    with op.batch_alter_table('external_party', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', mysql.VARCHAR(length=30), nullable=False))
        batch_op.add_column(sa.Column('email', mysql.VARCHAR(length=30), nullable=False))
        batch_op.create_index('phone', ['phone'], unique=True)
        batch_op.create_index('email', ['email'], unique=True)

    # ### end Alembic commands ###
