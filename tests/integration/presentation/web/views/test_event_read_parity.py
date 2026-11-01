"""Page and feed parity of the event reads (detail pages, iCal, manage list).

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

    requests["org_unknown_ical"] = url("main.organization_ical", id=4711)

    for organizer_id in range(1, 6):
        requests[f"organizer_{organizer_id}_ical"] = url(
            "main.organizer_ical", id=organizer_id
        )

    requests["organizer_unknown_ical"] = url("main.organizer_ical", id=4711)

    return requests


def test_event_page_payloads_match_snapshot(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    ids = seed_event_world(app, db, seeder)
    requests = _requests(utils, ids)
    actual = {}

    utils._access_token = None
    for key, url in requests.items():
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
