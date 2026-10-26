"""Add oauth2_code.acr and oauth2_code.amr

Revision ID: 3d1c7b9e5a42
Revises: 9f48493507e6
Create Date: 2026-10-26 21:00:00.000000

Authlib 1.6 adds both columns to OAuth2AuthorizationCodeMixin (OpenID
Connect acr/amr claims).

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3d1c7b9e5a42"
down_revision = "9f48493507e6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("oauth2_code", sa.Column("acr", sa.Text(), nullable=True))
    op.add_column("oauth2_code", sa.Column("amr", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("oauth2_code", "amr")
    op.drop_column("oauth2_code", "acr")
