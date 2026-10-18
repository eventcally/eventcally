"""The generated OpenAPI document must not change while dump schemas are decoupled
from the ORM models (`UPDATE_READ_PARITY=1` regenerates it for intended changes)."""

import json
import os

from tests.integration.presentation.api.read_parity import DATA_PATH


def _normalize(spec):
    """Path parameters come in nondeterministic order (route arguments are a set)."""
    for operations in spec.get("paths", {}).values():
        for operation in operations.values():
            if isinstance(operation, dict) and "parameters" in operation:
                operation["parameters"].sort(
                    key=lambda p: (p.get("in", ""), p.get("name", ""))
                )
    return spec


def test_openapi_document_matches_snapshot(utils):
    spec = _normalize(utils.get_ok("/swagger/").json)
    path = DATA_PATH / "openapi_snapshot.json"
    actual = json.dumps(spec, indent=2, sort_keys=True) + "\n"

    if os.environ.get("UPDATE_READ_PARITY") == "1":
        path.write_text(actual)
        return

    expected = json.dumps(
        _normalize(json.loads(path.read_text())), indent=2, sort_keys=True
    )
    assert actual == expected + "\n"
