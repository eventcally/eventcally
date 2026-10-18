"""Byte-level parity of the data dumps and the sitemap.

`data/dump_parity.json.gz` was captured from the ORM read path before the batch reads
moved to the query bus (`UPDATE_READ_PARITY=1`): the JSON files of the full dump and of
an organization dump, the checksums of the dumped images, and the sitemap.
"""

import gzip
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

from tests.integration.event_read_seed import seed_event_world
from tests.integration.seeder import Seeder

SNAPSHOT_PATH = Path(__file__).parent / "data" / "dump_parity.json.gz"


def _read_zip(path) -> dict:
    result = {}

    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            content = archive.read(name)

            if name.endswith(".json"):
                result[name] = json.loads(content)
            else:
                result[name] = hashlib.sha256(content).hexdigest()

    return result


def _normalized(value):
    """The legacy queries had no `ORDER BY`, so item order followed the physical row
    order and the id lists the join table order; the dumps now order by id, and the
    parity compares items by id and id lists sorted."""
    if isinstance(value, list) and value and isinstance(value[0], dict):
        items = [
            {
                key: sorted(item_value) if key.endswith("_ids") else item_value
                for key, item_value in item.items()
            }
            for item in value
        ]
        return sorted(items, key=lambda item: item["id"])

    return value


def _sitemap_urls(sitemap: str) -> list:
    return sorted(re.findall(r"<url>.*?</url>", sitemap))


def test_dumps_and_sitemap_match_snapshot(client, app, db, seeder: Seeder):
    ids = seed_event_world(app, db, seeder)
    actual = {}

    with app.app_context():
        from project.services.dump import dump_admin_unit, dump_all
        from project.services.seo import generate_sitemap
        from project.shared.paths import dump_org_path, dump_path, sitemap_path

        app.config["SERVER_NAME"] = "localhost"
        dump_all()
        dump_admin_unit(ids["a"])
        dump_admin_unit(ids["b"])

        actual["all"] = _read_zip(os.path.join(dump_path, "all.zip"))
        actual["org_a"] = _read_zip(os.path.join(dump_org_path, f"org-{ids['a']}.zip"))
        actual["org_b"] = _read_zip(os.path.join(dump_org_path, f"org-{ids['b']}.zip"))

        with app.test_request_context():
            generate_sitemap()

        actual["sitemap"] = Path(sitemap_path).read_text()

    if os.environ.get("UPDATE_READ_PARITY") == "1":  # pragma: no cover
        SNAPSHOT_PATH.write_bytes(
            gzip.compress(
                json.dumps(actual, indent=1, sort_keys=True).encode("utf-8"), mtime=0
            )
        )
        return

    expected = json.loads(gzip.decompress(SNAPSHOT_PATH.read_bytes()))

    if os.environ.get("PARITY_DIFF_FILE"):  # pragma: no cover
        with open(os.environ["PARITY_DIFF_FILE"], "w") as file:
            json.dump(actual, file, indent=1, sort_keys=True)

    assert sorted(actual) == sorted(expected)

    for key in expected:
        if key == "sitemap":
            assert _sitemap_urls(actual[key]) == _sitemap_urls(expected[key])
            continue

        assert sorted(actual[key]) == sorted(expected[key]), key

        for name in expected[key]:
            assert _normalized(actual[key][name]) == _normalized(expected[key][name]), (
                key,
                name,
            )
