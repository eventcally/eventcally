"""Byte-level parity of the place read endpoints.

The snapshot in `data/place_read_parity.json` was captured from the ORM read path
before place reads moved to the query bus. Regenerate it only for an intended API
change: `UPDATE_PLACE_READ_PARITY=1 ./runtests.sh ... -- <this file>`.

The `list_created_at_to` entry was regenerated deliberately: the legacy
`TrackableSearchParams.load_from_request` defaulted `last_modified_at_to` to
`created_at_to`, which dropped places updated after the bound. The query path bounds
each timestamp on its own, as for organizers.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import bindparam, text

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions

SNAPSHOT_PATH = Path(__file__).parent / "data" / "place_read_parity.json"


def _set_trackable(db, table, object_id, created_at, updated_at=None):
    db.session.execute(
        text(
            f"UPDATE {table} SET created_at = :created_at, updated_at = :updated_at"
            " WHERE id = :id"
        ),
        {"id": object_id, "created_at": created_at, "updated_at": updated_at},
    )


def seed_places(app, db, seeder: Seeder, admin_unit_id):
    """Places with fixed timestamps, so the payloads are deterministic."""
    from project.models import EventPlace, Location

    full_id = seeder.upsert_event_place(admin_unit_id, "Stadthalle")
    alpha_id = seeder.upsert_event_place(admin_unit_id, "Alpha")
    lake_id = seeder.upsert_event_place(admin_unit_id, "halle am See")
    central_id = seeder.upsert_event_place(admin_unit_id, "Zentrale Halle")
    bravo_id = seeder.upsert_event_place(admin_unit_id, "Bravo")
    image_id = seeder.upsert_default_image()

    with app.app_context():
        full = db.session.get(EventPlace, full_id)
        full.url = "https://example.com"
        full.description = "Die große Halle"
        full.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            state="Niedersachsen",
            country="DE",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        full.photo_id = image_id

        central = db.session.get(EventPlace, central_id)
        central.location = Location(city="Hamburg")
        db.session.commit()

        db.session.execute(
            text(
                "UPDATE image SET copyright_text = 'EventCally', license_id = 2"
                " WHERE id = :id"
            ),
            {"id": image_id},
        )
        _set_trackable(db, "image", image_id, datetime(2026, 1, 2, 8, 30))
        _set_trackable(
            db,
            "eventplace",
            full_id,
            datetime(2026, 1, 1, 10),
            datetime(2026, 3, 1, 12),
        )
        _set_trackable(db, "eventplace", alpha_id, datetime(2026, 2, 1, 9))
        _set_trackable(
            db,
            "eventplace",
            lake_id,
            datetime(2026, 1, 15, 14),
            datetime(2026, 2, 20, 16),
        )
        _set_trackable(db, "eventplace", central_id, datetime(2026, 1, 10, 7))
        _set_trackable(db, "eventplace", bravo_id, datetime(2026, 3, 5, 18))
        # The place created by the base setup carries the wall-clock time.
        db.session.execute(
            text(
                "UPDATE eventplace SET created_at = :created_at"
                " WHERE admin_unit_id = :admin_unit_id AND id NOT IN :ids"
            ).bindparams(bindparam("ids", expanding=True)),
            {
                "admin_unit_id": admin_unit_id,
                "created_at": datetime(2026, 1, 20, 11),
                "ids": [full_id, alpha_id, lake_id, central_id, bravo_id],
            },
        )
        db.session.commit()

    return {
        "full": full_id,
        "alpha": alpha_id,
        "lake": lake_id,
        "central": central_id,
        "bravo": bravo_id,
    }


def _requests(utils: UtilActions, admin_unit_id, other_admin_unit_id, ids):
    def org_list(**kwargs):
        return utils.get_url(
            "api_v1_organization_place_list", id=admin_unit_id, **kwargs
        )

    return {
        "list": org_list(),
        "list_other_org": utils.get_url(
            "api_v1_organization_place_list", id=other_admin_unit_id
        ),
        "list_name": org_list(name="halle"),
        "list_name_sort_created_at": org_list(name="Halle", sort="-created_at"),
        "list_name_sort_name": org_list(name="halle", sort="name"),
        "list_sort_name": org_list(sort="name"),
        "list_sort_created_at": org_list(sort="-created_at"),
        "list_sort_updated_at": org_list(sort="-updated_at"),
        "list_sort_last_modified_at": org_list(sort="-last_modified_at"),
        "list_created_at_from": org_list(created_at_from="2026-01-12T00:00:00"),
        "list_created_at_to": org_list(created_at_to="2026-01-31T00:00:00"),
        "list_updated_at_range": org_list(
            updated_at_from="2026-02-01T00:00:00", updated_at_to="2026-02-28T00:00:00"
        ),
        "list_last_modified_at_range": org_list(
            last_modified_at_from="2026-02-01T00:00:00",
            last_modified_at_to="2026-03-02T00:00:00",
        ),
        "list_page_2": org_list(page=2, per_page=2),
        "list_last_page": org_list(page=3, per_page=2),
        "list_out_of_range": org_list(page=4, per_page=2),
        "list_unknown_org": utils.get_url("api_v1_organization_place_list", id=4711),
        "detail_full": utils.get_url("api_v1_place", id=ids["full"]),
        "detail_bare": utils.get_url("api_v1_place", id=ids["alpha"]),
        "detail_city_only": utils.get_url("api_v1_place", id=ids["central"]),
        "detail_unknown": utils.get_url("api_v1_place", id=4711),
    }


def _capture(utils: UtilActions, url):
    response = utils.get_json(url)
    return {
        "url": url,
        "status": response.status_code,
        "etag": response.headers.get("ETag"),
        "body": response.get_data(as_text=True) if response.status_code == 200 else "",
    }


def test_place_read_payloads_match_snapshot(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    _, admin_unit_id = seeder.setup_api_access(user_access=False)
    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    seeder.upsert_event_place(other_admin_unit_id, "Halle B")
    ids = seed_places(app, db, seeder, admin_unit_id)

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE eventplace SET created_at = :created_at"
                " WHERE admin_unit_id = :admin_unit_id"
            ),
            {"admin_unit_id": other_admin_unit_id, "created_at": datetime(2026, 1, 5)},
        )
        db.session.commit()

    actual = {
        key: _capture(utils, url)
        for key, url in _requests(
            utils, admin_unit_id, other_admin_unit_id, ids
        ).items()
    }

    if os.environ.get("UPDATE_PLACE_READ_PARITY"):  # pragma: no cover
        SNAPSHOT_PATH.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False) + "\n"
        )

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert actual.keys() == expected.keys()

    for key in expected:
        assert actual[key] == expected[key], key
