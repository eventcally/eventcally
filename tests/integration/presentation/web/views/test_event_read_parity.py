"""Page and feed parity of the event reads (detail pages, iCal, widget, manage list).

`data/event_read_parity.json.gz` was captured from the ORM read path before event reads
moved to the query bus (`UPDATE_READ_PARITY=1`). HTML is compared after removing CSRF
tokens and nonces; iCal feeds byte for byte. Every request runs anonymously and as a
member of organization A, because visibility depends on the caller.
"""

import difflib
import gzip
import json
import os
import re
from pathlib import Path

from tests.integration.event_read_seed import seed_event_world
from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions

SNAPSHOT_PATH = Path(__file__).parent / "data" / "event_read_parity.json.gz"


def _normalize(text: str) -> str:
    text = re.sub(r'(csrf_token[^>]*value=")[^"]*"', r'\1"', text)
    text = re.sub(r'nonce="[^"]*"', 'nonce=""', text)
    # The default `date_from` of the event dates form is the day the test runs.
    text = re.sub(
        r'(id="date_from" name="date_from" value=")(?!2040)[0-9-]+"', r'\1TODAY"', text
    )
    text = re.sub(
        r'"[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{20,}"', '""', text
    )
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{2,}", "\n", text)


def _capture(utils: UtilActions, url):
    response = utils._client.get(url)
    return {
        "url": url,
        "status": response.status_code,
        "location": response.headers.get("Location"),
        "body": (
            _normalize(response.get_data(as_text=True))
            if response.status_code == 200
            else ""
        ),
    }


def _requests(utils: UtilActions, ids):
    def url(endpoint, **kwargs):
        return utils.get_url(endpoint, **kwargs)

    requests = {}

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
        requests[f"event_{name}"] = url("main.event", event_id=ids[name])
        requests[f"event_{name}_actions"] = url(
            "main.event_actions", event_id=ids[name]
        )
        requests[f"event_{name}_ical"] = url("main.event_ical", id=ids[name])

    requests["event_unknown"] = url("main.event", event_id=4711)
    requests["event_unknown_ical"] = url("main.event_ical", id=4711)
    requests["event_unknown_actions"] = url("main.event_actions", event_id=4711)

    for date_id in range(1, 21):
        requests[f"event_date_{date_id}"] = url("main.event_date", id=date_id)
        requests[f"event_date_{date_id}_ical"] = url("main.event_date_ical", id=date_id)

    requests["event_date_unknown"] = url("main.event_date", id=4711)
    requests["event_date_unknown_ical"] = url("main.event_date_ical", id=4711)

    for name in ("a", "b", "c"):
        requests[f"org_{name}_ical"] = url("main.organization_ical", id=ids[name])
        requests[f"org_{name}_widget"] = url("main.widget_event_dates", id=ids[name])

    requests["org_unknown_ical"] = url("main.organization_ical", id=4711)
    requests["org_unknown_widget"] = url("main.widget_event_dates", id=4711)

    widget_args = {
        "keyword": {"keyword": "Jam"},
        "category": {"category_id": 3},
        "page": {"page": 1, "per_page": 3},
        "date_from": {"date_from": "2040-04-01"},
        "styles": {"s_ft": "Arial", "s_bg": "#ffffff", "s_pr": "#112233"},
        "coordinate": {"coordinate": "51.9,10.4", "distance": 20000},
    }

    for key, args in widget_args.items():
        requests[f"org_a_widget_{key}"] = url(
            "main.widget_event_dates", id=ids["a"], **args
        )

    for organizer_id in range(1, 6):
        requests[f"organizer_{organizer_id}_ical"] = url(
            "main.organizer_ical", id=organizer_id
        )

    requests["organizer_unknown_ical"] = url("main.organizer_ical", id=4711)
    requests["event_dates_page"] = url("main.event_dates")
    requests["event_dates_page_filtered"] = url(
        "main.event_dates", keyword="Jam", date_from="2040-04-01"
    )

    manage_args = {
        "default": {},
        "page_2": {"page": 2},
        "keyword": {"keyword": "Jam"},
        "category": {"category_id": 3},
        "organizer": {"organizer_id": 1},
        "place": {"event_place_id": ids["rathaus"]},
        "tag": {"tag": "music"},
        "internal_tag": {"internal_tag": "secret"},
        "postal_code": {"postal_code": "38640,38690"},
        "date": {"date_from": "2040-03-01", "date_to": "2040-03-02"},
        "created_at": {"created_at_from": "2026-01-01", "created_at_to": "2026-01-05"},
        "radius": {
            "radius_location": "current_position",
            "radius_coordinate": "51.9077888,10.4333312",
            "radius_distance": 500,
            "radius_location_name": "Aktuelle Position",
        },
        "status": {"status": 1},
        "status_cancelled": {"status": -1},
        "public_status": {"public_status": 1},
        "recurring": {"is_recurring": "1"},
        "not_recurring": {"is_recurring": "0"},
        "sort_start": {"sort": "min_start"},
        "sort_modified": {"sort": "-last_modified_at"},
        "sort_created": {"sort": "-created_at"},
    }

    for key, args in manage_args.items():
        requests[f"manage_events_{key}"] = url(
            "manage_admin_unit.events", id=ids["a"], **args
        )

    return requests


def test_event_page_payloads_match_snapshot(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    ids = seed_event_world(app, db, seeder)
    requests = _requests(utils, ids)
    actual = {}

    utils._access_token = None
    for key, url in requests.items():
        if key.startswith("manage_"):
            continue
        actual[f"anon:{key}"] = _capture(utils, url)

    utils.login()
    for key, url in requests.items():
        actual[f"member:{key}"] = _capture(utils, url)

    if os.environ.get("UPDATE_READ_PARITY") == "1":  # pragma: no cover
        SNAPSHOT_PATH.write_bytes(
            gzip.compress(
                json.dumps(actual, indent=1, sort_keys=True).encode("utf-8"), mtime=0
            )
        )
        return

    expected = json.loads(gzip.decompress(SNAPSHOT_PATH.read_bytes()))
    assert sorted(actual) == sorted(expected)
    for entry in expected.values():
        entry["body"] = _normalize(entry["body"])
    mismatches = [key for key in sorted(expected) if actual[key] != expected[key]]
    diffs = {
        key: list(
            difflib.unified_diff(
                expected[key]["body"].splitlines(),
                actual[key]["body"].splitlines(),
                lineterm="",
                n=0,
            )
        )[:20]
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
