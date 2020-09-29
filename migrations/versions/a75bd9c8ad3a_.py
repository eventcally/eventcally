"""empty message

Revision ID: a75bd9c8ad3a
Revises: 51c47c7f0bdb
Create Date: 2020-09-29 16:53:02.520125

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import db
from sqlalchemy.dialects import postgresql
from models import EventReferenceRequestRejectionReason, EventReferenceRequestReviewStatus

# revision identifiers, used by Alembic.
revision = 'a75bd9c8ad3a'
down_revision = '51c47c7f0bdb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('eventreference',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('admin_unit_id', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['admin_unit_id'], ['adminunit.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('eventreferencerequest',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('admin_unit_id', sa.Integer(), nullable=False),
    sa.Column('review_status', db.IntegerEnum(EventReferenceRequestReviewStatus), nullable=True),
    sa.Column('rejection_reason', db.IntegerEnum(EventReferenceRequestRejectionReason), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['admin_unit_id'], ['adminunit.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('featuredevent')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('featuredevent',
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('event_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('review_status', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rejection_resaon', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rating', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_by_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('admin_unit_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['admin_unit_id'], ['adminunit.id'], name='featuredevent_admin_unit_id_fkey'),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name='featuredevent_created_by_id_fkey'),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], name='featuredevent_event_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='featuredevent_pkey')
    )
    op.drop_table('eventreferencerequest')
    op.drop_table('eventreference')
    # ### end Alembic commands ###
