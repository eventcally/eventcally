"""Byte-level parity of the organization invitation read endpoints.

The snapshot in `data/organization_invitation_read_parity.json` was captured from the
ORM read path before invitation reads moved to the query bus. Regenerate it only for an
intended API change:
`UPDATE_ORGANIZATION_INVITATION_READ_PARITY=1 ./runtests.sh ... -- <this file>`.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions

SNAPSHOT_PATH = (
    Path(__file__).parent / "data" / "organization_invitation_read_parity.json"
)


def _set_trackable(db, table, object_id, created_at, updated_at=None):
    db.session.execute(
        text(
            f"UPDATE {table} SET created_at = :created_at, updated_at = :updated_at"
            " WHERE id = :id"
        ),
        {"id": object_id, "created_at": created_at, "updated_at": updated_at},
    )


def seed_invitations(app, db, seeder: Seeder, admin_unit_id):
    """Invitations with fixed timestamps, so the payloads are deterministic."""
    full_id = seeder.create_admin_unit_invitation(
        admin_unit_id,
        email="full@test.de",
        admin_unit_name="Voll",
        relation_auto_verify_event_reference_requests=True,
        relation_verify=True,
    )
    alpha_id = seeder.create_admin_unit_invitation(
        admin_unit_id, email="alpha@test.de", admin_unit_name="Alpha"
    )
    bare_id = seeder.create_admin_unit_invitation(
        admin_unit_id, email="bare@test.de", admin_unit_name=None
    )
    bravo_id = seeder.create_admin_unit_invitation(
        admin_unit_id, email="bravo@test.de", admin_unit_name="Bravo"
    )

    with app.app_context():
        _set_trackable(
            db,
            "adminunitinvitation",
            full_id,
            datetime(2026, 1, 1, 10),
            datetime(2026, 3, 1, 12),
        )
        _set_trackable(db, "adminunitinvitation", alpha_id, datetime(2026, 2, 1, 9))
        _set_trackable(
            db,
            "adminunitinvitation",
            bare_id,
            datetime(2026, 1, 15, 14),
            datetime(2026, 2, 20, 16),
        )
        _set_trackable(db, "adminunitinvitation", bravo_id, datetime(2026, 3, 5, 18))
        db.session.commit()

    return {"full": full_id, "alpha": alpha_id, "bare": bare_id, "bravo": bravo_id}


def _requests(utils: UtilActions, admin_unit_id, other_admin_unit_id, ids, other_id):
    def inv_list(**kwargs):
        return utils.get_url(
            "api_v1_organization_organization_invitation_list",
            id=admin_unit_id,
            **kwargs,
        )

    return {
        "list": inv_list(),
        "list_sort_name": inv_list(sort="name"),
        "list_sort_created_at": inv_list(sort="-created_at"),
        "list_sort_updated_at": inv_list(sort="-updated_at"),
        "list_sort_last_modified_at": inv_list(sort="-last_modified_at"),
        "list_created_at_from": inv_list(created_at_from="2026-01-12T00:00:00"),
        "list_created_at_to": inv_list(created_at_to="2026-02-02T00:00:00"),
        "list_updated_at_range": inv_list(
            updated_at_from="2026-02-01T00:00:00", updated_at_to="2026-02-28T00:00:00"
        ),
        "list_last_modified_at_range": inv_list(
            last_modified_at_from="2026-02-01T00:00:00",
            last_modified_at_to="2026-03-02T00:00:00",
        ),
        "list_page_2": inv_list(page=2, per_page=2),
        "list_last_page": inv_list(page=2, per_page=3),
        "list_out_of_range": inv_list(page=4, per_page=2),
        "list_unknown_org": utils.get_url(
            "api_v1_organization_organization_invitation_list", id=4711
        ),
        "detail_full": utils.get_url("api_v1_organization_invitation", id=ids["full"]),
        "detail_bare": utils.get_url("api_v1_organization_invitation", id=ids["bare"]),
        "detail_unknown": utils.get_url("api_v1_organization_invitation", id=4711),
        "detail_other_org": utils.get_url(
            "api_v1_organization_invitation", id=other_id
        ),
    }


def _capture(utils: UtilActions, url):
    response = utils.get_json(url)
    return {
        "url": url,
        "status": response.status_code,
        "etag": response.headers.get("ETag"),
        "body": response.get_data(as_text=True) if response.status_code == 200 else "",
    }


def test_organization_invitation_read_payloads_match_snapshot(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    _, admin_unit_id = seeder.setup_api_access()
    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    other_id = seeder.create_admin_unit_invitation(
        other_admin_unit_id, email="other-invited@test.de"
    )
    ids = seed_invitations(app, db, seeder, admin_unit_id)

    actual = {
        key: _capture(utils, url)
        for key, url in _requests(
            utils, admin_unit_id, other_admin_unit_id, ids, other_id
        ).items()
    }

    if os.environ.get("UPDATE_ORGANIZATION_INVITATION_READ_PARITY"):  # pragma: no cover
        SNAPSHOT_PATH.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False) + "\n"
        )

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert actual.keys() == expected.keys()

    for key in expected:
        assert actual[key] == expected[key], key
