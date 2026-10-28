"""Parity of the select2 ajax lookups (`X-Backend-For-Frontend: ajax_lookup`).

The snapshot in `data/ajax_lookup_parity.json` was captured from the ORM loaders before
they moved to the query bus. Regenerate it only for an intended change:
`UPDATE_AJAX_LOOKUP_PARITY=1 ./runtests.sh ... -- <this file>`.
"""

import json
import os
from pathlib import Path

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions

SNAPSHOT_PATH = Path(__file__).parent / "data" / "ajax_lookup_parity.json"


def _lookup(utils: UtilActions, url, field_name, term="", **args):
    extra = "".join(f"&{key}={value}" for key, value in args.items())
    response = utils.get_json_ok(
        f"{url}?field_name={field_name}&term={term}{extra}",
        headers={"X-Backend-For-Frontend": "ajax_lookup"},
    )
    return response.json


def test_ajax_lookup_parity(client, app, db, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_admin_unit(other_user_id, "Another Crew")

    for name in ["Alpha", "Bravo", "crew am See", "Zentrale Crew", "Delta"]:
        seeder.upsert_event_organizer(admin_unit_id, name)
        seeder.upsert_event_place(admin_unit_id, name.replace("Crew", "Halle"))

    seeder.upsert_event_organizer(other_admin_unit_id, "Foreign Organizer")
    seeder.upsert_event_place(other_admin_unit_id, "Foreign Place")
    set_id, _ = seeder.get_one_custom_event_category_set()

    # Creates the default place of the organization the snapshot contains.
    seeder.create_event(admin_unit_id)
    event_url = utils.get_url("manage_admin_unit.event_legacy_create", id=admin_unit_id)

    captured = {
        "license": _lookup(utils, event_url, "photo-license"),
        "license_term": _lookup(utils, event_url, "photo-license", "cc"),
        "license_page_2": _lookup(
            utils, event_url, "photo-license", "", per_page=2, page=2
        ),
        "categories": _lookup(utils, event_url, "categories"),
        "categories_term": _lookup(utils, event_url, "categories", "Ev"),
        "categories_page_2": _lookup(
            utils, event_url, "categories", "", per_page=3, page=2
        ),
        "custom_categories": _lookup(
            utils, event_url, f"custom_categories-set_{set_id}"
        ),
        "custom_categories_term": _lookup(
            utils, event_url, f"custom_categories-set_{set_id}", "a"
        ),
        "organizer": _lookup(utils, event_url, "organizer"),
        "organizer_term": _lookup(utils, event_url, "organizer", "crew"),
        "organizer_page_2": _lookup(
            utils, event_url, "organizer", "", per_page=2, page=2
        ),
        "co_organizers": _lookup(utils, event_url, "co_organizers", "a"),
        "event_place": _lookup(utils, event_url, "event_place"),
        "event_place_term": _lookup(utils, event_url, "event_place", "halle"),
    }

    if os.environ.get("UPDATE_AJAX_LOOKUP_PARITY"):
        # Ids are database ids; keep them, the seed is deterministic per test.
        SNAPSHOT_PATH.parent.mkdir(exist_ok=True)
        SNAPSHOT_PATH.write_text(
            json.dumps(captured, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert json.loads(json.dumps(captured)) == expected


def test_lookup_out_of_range_page_is_404(client, app, db, utils: UtilActions, seeder):
    _, admin_unit_id = seeder.setup_base()
    url = utils.get_url("manage_admin_unit.event_legacy_create", id=admin_unit_id)

    response = client.get(
        f"{url}?field_name=photo-license&term=&page=9",
        headers={"X-Backend-For-Frontend": "ajax_lookup"},
    )

    assert response.status_code == 404


def test_get_one_ignores_a_non_numeric_value(app, db):
    from project.presentation.web.modular.ajax import LicenseAjaxModelLoader

    with app.test_request_context():
        assert LicenseAjaxModelLoader().get_one("not-a-number") is None
        assert LicenseAjaxModelLoader().get_one(None) is None
        license = LicenseAjaxModelLoader().get_one("1")
        assert license.code == "CC0 1.0"
        assert LicenseAjaxModelLoader().format(license)[0] == 1
