"""init tables

Revision ID: 7bd2c4782608
Revises: d4dc04f2aaaf
Create Date: 2020-05-21 16:57:41.122224

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7bd2c4782608'
down_revision = 'd4dc04f2aaaf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ih_order',
    sa.Column('create_time', sa.DateTime(), nullable=True),
    sa.Column('modify_time', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('house_id', sa.Integer(), nullable=False),
    sa.Column('begin_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('days', sa.Integer(), nullable=False),
    sa.Column('house_price', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('WAIT_ACCEPT', 'WAIT_PAYMENT', 'PAID', 'WAIT_COMMENT', 'COMPLETE', 'CANCELED', 'REJECTED'), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['house_id'], ['ih_house.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['ih_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ih_order_status'), 'ih_order', ['status'], unique=False)
    op.drop_index('ix_hi_order_status', table_name='hi_order')
    op.drop_table('hi_order')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hi_order',
    sa.Column('create_time', mysql.DATETIME(), nullable=True),
    sa.Column('modify_time', mysql.DATETIME(), nullable=True),
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('user_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('house_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('begin_date', mysql.DATETIME(), nullable=False),
    sa.Column('end_date', mysql.DATETIME(), nullable=False),
    sa.Column('days', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('house_price', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('amount', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('status', mysql.ENUM('WAIT_ACCEPT', 'WAIT_PAYMENT', 'PAID', 'WAIT_COMMENT', 'COMPLETE', 'CANCELED', 'REJECTED'), nullable=True),
    sa.Column('comment', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['house_id'], ['ih_house.id'], name='hi_order_ibfk_1'),
    sa.ForeignKeyConstraint(['user_id'], ['ih_user.id'], name='hi_order_ibfk_2'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_hi_order_status', 'hi_order', ['status'], unique=False)
    op.drop_index(op.f('ix_ih_order_status'), table_name='ih_order')
    op.drop_table('ih_order')
    # ### end Alembic commands ###
