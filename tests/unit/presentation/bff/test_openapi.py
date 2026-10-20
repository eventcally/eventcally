import json
from pathlib import Path

from project.presentation.bff.openapi import build_openapi


def test_users_path():
    spec = build_openapi()

    assert spec["openapi"] == "3.1.0"
    operation = spec["paths"]["/bff/admin/users"]["get"]
    assert {p["name"] for p in operation["parameters"]} == {"page", "per_page"}
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AdminUserPage"
    }
    assert "AdminUserPage" in spec["components"]["schemas"]
    assert "ErrorResponse" in spec["components"]["schemas"]


def test_committed_spec_is_up_to_date():
    path = Path(__file__).parents[4] / "frontend" / "openapi.json"
    committed = json.loads(path.read_text(encoding="utf-8"))

    assert committed == build_openapi(), (
        "frontend/openapi.json is stale: run "
        "`python -m project.presentation.bff.openapi > frontend/openapi.json` "
        "and `npm run gen:api --prefix frontend`"
    )


def test_main_prints_json(capsys):
    import runpy

    runpy.run_module("project.presentation.bff.openapi", run_name="__main__")

    assert json.loads(capsys.readouterr().out)["openapi"] == "3.1.0"
