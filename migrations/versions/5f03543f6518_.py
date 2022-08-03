"""empty message

Revision ID: 5f03543f6518
Revises: 370b9ebf9ff3
Create Date: 2022-08-01 13:02:27.893929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f03543f6518'
down_revision = '370b9ebf9ff3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('phone_number', sa.Unicode(length=255), nullable=True))
    op.add_column('Venue', sa.Column('phone_country_code', sa.Unicode(length=8), nullable=True))
    op.drop_column('Venue', 'phone')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('phone', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    op.drop_column('Venue', 'phone_country_code')
    op.drop_column('Venue', 'phone_number')
    # ### end Alembic commands ###
