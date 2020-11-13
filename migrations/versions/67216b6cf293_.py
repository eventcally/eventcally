"""empty message

Revision ID: 67216b6cf293
Revises: a336ac384c64
Create Date: 2020-08-01 15:43:11.377833

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from project import dbtypes
from project.models import EventRejectionReason, EventReviewStatus


# revision identifiers, used by Alembic.
revision = '67216b6cf293'
down_revision = 'a336ac384c64'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('rejection_resaon', dbtypes.IntegerEnum(EventRejectionReason), nullable=True))
    op.add_column('event', sa.Column('review_status', dbtypes.IntegerEnum(EventReviewStatus), nullable=True))
    op.drop_column('event', 'verified')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('verified', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('event', 'review_status')
    op.drop_column('event', 'rejection_resaon')
    # ### end Alembic commands ###
