"""Shared helpers for byte-level API read parity snapshots.

A snapshot is captured on the ORM read path before an endpoint moves to the query bus
and committed under `tests/api/data/<name>_read_parity.json`. Regenerate one only for
an intended API change: `UPDATE_READ_PARITY=1 ./runtests.sh ... -- <test file>`.
"""

import json
import os
from pathlib import Path

from sqlalchemy import text

DATA_PATH = Path(__file__).parent / "data"


def set_trackable(db, table, object_id, created_at, updated_at=None):
    db.session.execute(
        text(
            f"UPDATE {table} SET created_at = :created_at, updated_at = :updated_at"
            " WHERE id = :id"
        ),
        {"id": object_id, "created_at": created_at, "updated_at": updated_at},
    )


def capture(utils, url):
    response = utils.get_json(url)
    return {
        "url": url,
        "status": response.status_code,
        "etag": response.headers.get("ETag"),
        "body": response.get_data(as_text=True) if response.status_code == 200 else "",
    }


def assert_matches_snapshot(name, utils, requests: dict):
    actual = {key: capture(utils, url) for key, url in requests.items()}
    path = DATA_PATH / f"{name}_read_parity.json"

    if os.environ.get("UPDATE_READ_PARITY") == "1":
        path.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
        return

    expected = json.loads(path.read_text())
    assert sorted(actual) == sorted(expected)

    mismatches = [key for key in sorted(expected) if actual[key] != expected[key]]
    assert mismatches == [], {key: actual[key] for key in mismatches}
