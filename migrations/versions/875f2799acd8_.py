"""empty message

Revision ID: 875f2799acd8
Revises: ff654866893f
Create Date: 2025-06-28 13:44:01.952517

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "875f2799acd8"
down_revision = "ff654866893f"
branch_labels = None
depends_on = None

legacy_scope_mapping = {
    "organizer:write": "organization.event_organizers:write",
    "place:write": "organization.event_places:write",
    "event:write": "organization.events:write",
    "user:read": "user.organization_invitations:read user.favorite_events:read",
    "user:write": "user.organization_invitations:write user.favorite_events:write",
}


def upgrade():
    for legacy_scope, new_scope in legacy_scope_mapping.items():
        op.execute(
            sa.text(
                f"UPDATE oauth2_client SET client_metadata = REPLACE(client_metadata, '{legacy_scope}', '{new_scope}')"
            )
        )
        op.execute(
            sa.text(
                f"UPDATE oauth2_token SET scope = REPLACE(scope, '{legacy_scope}', '{new_scope}')"
            )
        )


def downgrade():
    for legacy_scope, new_scope in legacy_scope_mapping.items():
        op.execute(
            sa.text(
                f"UPDATE oauth2_client SET client_metadata = REPLACE(client_metadata, '{new_scope}', '{legacy_scope}')"
            )
        )
        op.execute(
            sa.text(
                f"UPDATE oauth2_token SET scope = REPLACE(scope, '{new_scope}', '{legacy_scope}')"
            )
        )
