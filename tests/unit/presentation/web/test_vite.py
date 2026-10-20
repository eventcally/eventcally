import json

import pytest
from flask import Flask

from project.presentation.web import vite
from project.presentation.web.vite import vite_entry

MANIFEST = {
    "src/apps/admin/main.ts": {
        "file": "assets/admin-abc.js",
        "name": "admin",
        "isEntry": True,
        "css": ["assets/admin-abc.css"],
        "imports": ["_shared.js"],
    },
    "_shared.js": {"file": "assets/shared-def.js", "css": ["assets/shared-def.css"]},
}


@pytest.fixture
def vite_app(tmp_path):
    app = Flask("project", static_folder="presentation/web/static")
    app.config["SERVER_NAME"] = "localhost"
    app.config["VITE_DEV_SERVER_URL"] = ""
    app.config["FLASK_DEBUG"] = True
    dist = tmp_path / "presentation" / "web" / "static" / "dist" / ".vite"
    dist.mkdir(parents=True)
    app.root_path = str(tmp_path)
    vite._manifest_cache.clear()
    return app, dist


def test_prod_tags(vite_app):
    app, dist = vite_app
    (dist / "manifest.json").write_text(json.dumps(MANIFEST))

    with app.test_request_context():
        html = str(vite_entry("admin"))

    assert 'rel="stylesheet" href="/static/dist/assets/admin-abc.css"' in html
    assert 'rel="stylesheet" href="/static/dist/assets/shared-def.css"' in html
    assert 'rel="modulepreload" href="/static/dist/assets/shared-def.js"' in html
    assert '<script type="module" src="/static/dist/assets/admin-abc.js">' in html


def test_dev_tags(vite_app):
    app, _ = vite_app
    app.config["VITE_DEV_SERVER_URL"] = "http://localhost:5173/"

    with app.test_request_context():
        html = str(vite_entry("admin"))

    assert 'src="http://localhost:5173/static/dist/@vite/client"' in html
    assert 'src="http://localhost:5173/static/dist/src/apps/admin/main.ts"' in html


def test_missing_manifest_renders_comment(vite_app):
    app, _ = vite_app

    with app.test_request_context():
        html = str(vite_entry("admin"))

    assert html == "<!-- vite entry 'admin' not built -->"


def test_unknown_entry_renders_comment(vite_app):
    app, dist = vite_app
    (dist / "manifest.json").write_text(json.dumps(MANIFEST))

    with app.test_request_context():
        html = str(vite_entry("other"))

    assert html == "<!-- vite entry 'other' not built -->"


def test_manifest_is_cached_outside_debug(vite_app):
    app, dist = vite_app
    app.config["FLASK_DEBUG"] = False
    (dist / "manifest.json").write_text(json.dumps(MANIFEST))

    with app.test_request_context():
        first = str(vite_entry("admin"))
        (dist / "manifest.json").unlink()
        second = str(vite_entry("admin"))

    assert first == second


def test_unknown_and_repeated_imports_are_skipped(vite_app):
    app, dist = vite_app
    manifest = {
        **MANIFEST,
        "src/apps/admin/main.ts": {
            **MANIFEST["src/apps/admin/main.ts"],
            "imports": ["_shared.js", "_shared.js", "_missing.js"],
        },
    }
    (dist / "manifest.json").write_text(json.dumps(manifest))

    with app.test_request_context():
        html = str(vite_entry("admin"))

    assert html.count('rel="modulepreload"') == 1
