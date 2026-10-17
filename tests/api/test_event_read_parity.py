"""Byte-level parity of the event and event-date read endpoints.

`data/event_read_parity.json` was captured from the ORM read path before event reads
moved to the query bus (`UPDATE_READ_PARITY=1`). Every request runs anonymously and as
a member of organization A, because visibility depends on the caller.
"""

import difflib
import json
import os

from project.extensions import limiter
from tests.api import read_parity
from tests.event_read_seed import seed_event_world
from tests.seeder import Seeder
from tests.utils import UtilActions

UNORDERED_LISTS = ("categories", "co_organizers", "custom_categories")


def _sort_unordered(value):
    """The order of categories and co-organizers is whatever the join table yields,
    so the parity compares them by id."""
    if isinstance(value, dict):
        return {
            key: (
                sorted((_sort_unordered(item) for item in items), key=lambda i: i["id"])
                if key in UNORDERED_LISTS and isinstance(items, list)
                else _sort_unordered(items)
            )
            for key, items in value.items()
        }

    if isinstance(value, list):
        return [_sort_unordered(item) for item in value]

    return value


def _comparable(capture: dict) -> dict:
    body = json.loads(capture["body"]) if capture["body"] else None
    return {
        "url": capture["url"],
        "status": capture["status"],
        "body": json.dumps(_sort_unordered(body), sort_keys=True),
    }


def _requests(utils: UtilActions, ids):
    def url(endpoint, **kwargs):
        return utils.get_url(endpoint, **kwargs)

    org_a = ids["a"]
    search_args = {
        "default": {},
        "page_2": {"page": 2, "per_page": 3},
        "keyword_name": {"keyword": "Jam"},
        "keyword_city": {"keyword": "Goslar"},
        "keyword_description": {"keyword": "Beschreibung"},
        "tag": {"tag": "music"},
        "tags_all": {"tag": ["music", "live"]},
        "internal_tag": {"internal_tag": "secret"},
        "date_range": {"date_from": "2040-03-01", "date_to": "2040-03-02"},
        "date_from": {"date_from": "2040-04-01"},
        "distance": {"coordinate": "51.9,10.4", "distance": 20000},
        "category": {"category_id": [1, 3]},
        "custom_category_set": {"custom_category_set_id": 1},
        "weekday": {"weekday": [4]},
        "organization": {"organization_id": org_a},
        "organizer": {"organizer_id": 1},
        "place": {"event_place_id": ids["rathaus"]},
        "sort_rating": {"sort": "-rating"},
        "sort_start": {"sort": "start"},
        "sort_created": {"sort": "-created_at"},
        "sort_updated": {"sort": "-updated_at"},
        "sort_modified": {"sort": "-last_modified_at"},
        "sort_reference": {
            "sort": "-reference_created_at",
            "organization_id": org_a,
            "include_organization_references": 1,
        },
        "status": {"status": "cancelled"},
        "public_status": {"public_status": ["draft", "planned"]},
        "postal_code": {"postal_code": "386"},
        "exclude_recurring": {"exclude_recurring": 1},
        "references_included": {
            "organization_id": org_a,
            "include_organization_references": 1,
        },
        "references_only": {
            "organization_id": org_a,
            "organization_references_only": 1,
        },
        "created_range": {
            "created_at_from": "2026-01-03T00:00:00",
            "created_at_to": "2026-01-09T00:00:00",
        },
    }
    requests = {}

    for key, args in search_args.items():
        requests[f"events_search_{key}"] = url("api_v1_event_search", **args)
        requests[f"event_dates_search_{key}"] = url("api_v1_event_date_search", **args)
        requests[f"org_events_search_{key}"] = url(
            "api_v1_organization_event_search", id=org_a, **args
        )
        requests[f"org_event_dates_search_{key}"] = url(
            "api_v1_organization_event_date_search", id=org_a, **args
        )

    requests["event_dates_search_not_referenced"] = url(
        "api_v1_event_date_search", not_referenced=1
    )

    list_args = {
        "default": {},
        "page_2": {"page": 2, "per_page": 3},
        "sort_created": {"sort": "-created_at"},
        "sort_updated": {"sort": "-updated_at"},
        "sort_modified": {"sort": "-last_modified_at"},
        "sort_start": {"sort": "start"},
        "created_from": {"created_at_from": "2026-01-04T00:00:00"},
        "updated_range": {
            "updated_at_from": "2026-02-01T00:00:00",
            "updated_at_to": "2026-02-01T12:00:00",
        },
        "last_modified_to": {"last_modified_at_to": "2026-02-01T12:00:00"},
    }

    for key, args in list_args.items():
        requests[f"events_list_{key}"] = url("api_v1_event_list", **args)
        requests[f"event_dates_list_{key}"] = url("api_v1_event_date_list", **args)

        for name in ("a", "b", "c"):
            requests[f"org_{name}_events_list_{key}"] = url(
                "api_v1_organization_event_list", id=ids[name], **args
            )

    requests["org_unknown_events_list"] = url("api_v1_organization_event_list", id=4711)
    requests["org_unknown_events_search"] = url(
        "api_v1_organization_event_search", id=4711
    )
    requests["org_unknown_event_dates_search"] = url(
        "api_v1_organization_event_date_search", id=4711
    )

    for name in (
        "full",
        "recurring",
        "allday",
        "draft",
        "planned",
        "cancelled",
        "past",
        "other",
        "unverified",
    ):
        requests[f"event_{name}"] = url("api_v1_event", id=ids[name])
        requests[f"event_{name}_dates"] = url("api_v1_event_dates", id=ids[name])

    requests["event_dates_page"] = url(
        "api_v1_event_dates", id=ids["recurring"], page=2, per_page=2
    )
    requests["event_unknown"] = url("api_v1_event", id=4711)
    requests["event_unknown_dates"] = url("api_v1_event_dates", id=4711)

    for date_id in range(1, 21):
        requests[f"event_date_{date_id}"] = url("api_v1_event_date", id=date_id)

    requests["event_date_unknown"] = url("api_v1_event_date", id=4711)
    return requests


def test_event_read_payloads_match_snapshot(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    ids = seed_event_world(app, db, seeder)
    requests = _requests(utils, ids)
    token = utils._access_token
    actual = {}
    app.config["API_READ_ANONYM"] = True

    utils._access_token = None
    for key, url in requests.items():
        with app.app_context():  # the anonymous limit is 60 requests per minute
            limiter.reset()
        actual[f"anon:{key}"] = read_parity.capture(utils, url)

    utils._access_token = token
    for key, url in requests.items():
        actual[f"auth:{key}"] = read_parity.capture(utils, url)

    path = read_parity.DATA_PATH / "event_read_parity.json"

    if os.environ.get("UPDATE_READ_PARITY") == "1":  # pragma: no cover
        path.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
        return

    expected = json.loads(path.read_text())
    assert sorted(actual) == sorted(expected)
    mismatches = [
        key
        for key in sorted(expected)
        if _comparable(actual[key]) != _comparable(expected[key])
    ]
    diffs = {
        key: list(
            difflib.unified_diff(
                json.dumps(
                    json.loads(expected[key]["body"] or "null"),
                    indent=1,
                    sort_keys=True,
                ).splitlines(),
                json.dumps(
                    json.loads(actual[key]["body"] or "null"), indent=1, sort_keys=True
                ).splitlines(),
                lineterm="",
                n=0,
            )
        )[:16]
        for key in mismatches[:2]
    }
    if mismatches and os.environ.get("PARITY_DIFF_FILE"):  # pragma: no cover
        with open(os.environ["PARITY_DIFF_FILE"], "w") as file:
            json.dump(
                {
                    key: {"expected": expected[key], "actual": actual[key]}
                    for key in mismatches
                },
                file,
                indent=1,
            )

    assert mismatches == [], (mismatches, diffs)
