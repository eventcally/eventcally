"""empty message

Revision ID: 92f37474ad62
Revises: 0a282a331e35
Create Date: 2020-10-18 13:06:47.639083

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "92f37474ad62"
down_revision = "0a282a331e35"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_table('spatial_ref_sys')
    op.execute(
        "ALTER TABLE eventplace DROP CONSTRAINT IF EXISTS eventplace_name_organizer_id_admin_unit_id_key;"
    )
    # op.drop_constraint(
    #     "eventplace_name_organizer_id_admin_unit_id_key", "eventplace", type_="unique"
    # )
    op.execute(
        "ALTER TABLE eventplace DROP CONSTRAINT IF EXISTS eventplace_organizer_id_fkey;"
    )
    op.execute(
        "ALTER TABLE eventplace DROP CONSTRAINT IF EXISTS fk_eventplace_organizer_id;"
    )
    # op.drop_constraint("eventplace_organizer_id_fkey", "eventplace", type_="foreignkey")
    op.drop_column("eventplace", "public")
    op.drop_column("eventplace", "organizer_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "eventplace",
        sa.Column("organizer_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "eventplace",
        sa.Column("public", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "eventplace_organizer_id_fkey",
        "eventplace",
        "eventorganizer",
        ["organizer_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "eventplace_name_organizer_id_admin_unit_id_key",
        "eventplace",
        ["name", "organizer_id", "admin_unit_id"],
    )
    op.create_table(
        "spatial_ref_sys",
        sa.Column("srid", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "auth_name", sa.VARCHAR(length=256), autoincrement=False, nullable=True
        ),
        sa.Column("auth_srid", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "srtext", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
        ),
        sa.Column(
            "proj4text", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
        ),
        sa.CheckConstraint(
            "(srid > 0) AND (srid <= 998999)", name="spatial_ref_sys_srid_check"
        ),
        sa.PrimaryKeyConstraint("srid", name="spatial_ref_sys_pkey"),
    )
    # ### end Alembic commands ###
