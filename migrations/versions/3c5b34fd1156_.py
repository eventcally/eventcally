"""empty message

Revision ID: 3c5b34fd1156
Revises: 27da3ceea723
Create Date: 2020-11-08 19:11:32.132404

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy import orm
from sqlalchemy.orm import declarative_base

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "3c5b34fd1156"
down_revision = "27da3ceea723"
branch_labels = None
depends_on = None

Base = declarative_base()


class Event(Base):
    __tablename__ = "event"
    id = sa.Column(sa.Integer(), primary_key=True)
    category_id = sa.Column(
        sa.Integer, sa.ForeignKey("eventcategory.id"), nullable=False
    )
    category = orm.relationship("EventCategory", uselist=False)
    categories = orm.relationship("EventCategory", secondary="event_eventcategories")


class EventEventCategories(Base):
    __tablename__ = "event_eventcategories"
    id = sa.Column(sa.Integer(), primary_key=True)
    event_id = sa.Column(sa.Integer, sa.ForeignKey("event.id"), nullable=False)
    category_id = sa.Column(
        sa.Integer, sa.ForeignKey("eventcategory.id"), nullable=False
    )


class EventCategory(Base):
    __tablename__ = "eventcategory"
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.Unicode(255), nullable=False, unique=True)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "event_eventcategories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["eventcategory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    upgrade_category_to_categories()

    # op.drop_table('spatial_ref_sys')
    op.drop_constraint("event_category_id_fkey", "event", type_="foreignkey")
    op.drop_column("event", "category_id")
    # ### end Alembic commands ###


def upgrade_category_to_categories():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for event in session.query(Event):
        event.categories = [event.category]

    session.commit()


def downgrade_categories_to_category():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for event in session.query(Event):
        event.category = event.categories[0]

    session.commit()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "event",
        sa.Column("category_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    downgrade_categories_to_category()
    op.alter_column(
        "event",
        sa.Column(
            "category_id",
            existing_type=sa.INTEGER(),
            autoincrement=False,
            nullable=False,
        ),
    )

    op.create_foreign_key(
        "event_category_id_fkey", "event", "eventcategory", ["category_id"], ["id"]
    )
    # op.create_table(
    #     "spatial_ref_sys",
    #     sa.Column("srid", sa.INTEGER(), autoincrement=False, nullable=False),
    #     sa.Column(
    #         "auth_name", sa.VARCHAR(length=256), autoincrement=False, nullable=True
    #     ),
    #     sa.Column("auth_srid", sa.INTEGER(), autoincrement=False, nullable=True),
    #     sa.Column(
    #         "srtext", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
    #     ),
    #     sa.Column(
    #         "proj4text", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
    #     ),
    #     sa.CheckConstraint(
    #         "(srid > 0) AND (srid <= 998999)", name="spatial_ref_sys_srid_check"
    #     ),
    #     sa.PrimaryKeyConstraint("srid", name="spatial_ref_sys_pkey"),
    # )
    op.drop_table("event_eventcategories")
    # ### end Alembic commands ###
