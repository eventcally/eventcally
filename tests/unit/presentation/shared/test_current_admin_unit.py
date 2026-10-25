from types import SimpleNamespace

import pytest
from flask import Flask, g
from flask_login.utils import encode_cookie

from project.presentation.shared import current_admin_unit as module

UNIT = SimpleNamespace(id=3)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    return app


@pytest.fixture
def authenticated(monkeypatch):
    monkeypatch.setattr(module, "current_user", SimpleNamespace(is_authenticated=True))
    monkeypatch.setattr(module, "get_admin_unit_for_manage", lambda id: UNIT)
    monkeypatch.setattr(module, "get_admin_units_for_manage", lambda: [UNIT])


def test_set_current_admin_unit_ignores_none(app):
    with app.test_request_context():
        module.set_current_admin_unit(None)
        assert not hasattr(g, "manage_admin_unit")

        module.set_current_admin_unit(UNIT)
        assert g.manage_admin_unit is UNIT


def test_returns_the_unit_already_on_g(app):
    with app.test_request_context():
        g.manage_admin_unit = UNIT
        assert module.get_current_admin_unit() is UNIT


def test_anonymous_has_no_unit(app, monkeypatch):
    monkeypatch.setattr(module, "current_user", SimpleNamespace(is_authenticated=False))

    with app.test_request_context():
        assert module.get_current_admin_unit() is None


def test_falls_back_to_the_first_manageable_unit(app, authenticated):
    with app.test_request_context():
        assert module.get_current_admin_unit() is UNIT
        assert g.manage_admin_unit is UNIT


def test_no_fallback_when_disabled_or_nothing_manageable(
    app, authenticated, monkeypatch
):
    with app.test_request_context():
        assert module.get_current_admin_unit(fallback=False) is None

    monkeypatch.setattr(module, "get_admin_units_for_manage", lambda: [])
    with app.test_request_context():
        assert module.get_current_admin_unit() is None


def test_reads_the_unit_from_the_cookie(app, authenticated):
    with app.app_context():
        cookie = encode_cookie("3")

    with app.test_request_context(headers={"Cookie": f"manage_admin_unit_id={cookie}"}):
        assert module.get_current_admin_unit(fallback=False) is UNIT


def test_invalid_cookie_is_ignored(app, authenticated):
    with app.test_request_context(headers={"Cookie": "manage_admin_unit_id=garbage"}):
        assert module.get_current_admin_unit_from_cookies() is None

    with app.test_request_context():
        assert module.get_current_admin_unit_from_cookies() is None


def test_api_reads_the_unit_from_the_header_only(app, authenticated):
    with app.test_request_context(headers={"X-OrganizationId": "3"}):
        assert module.get_current_admin_unit_for_api() is UNIT

    with app.test_request_context(headers={"X-OrganizationId": "x"}):
        assert module.get_current_admin_unit_from_headers() is None

    with app.test_request_context():
        assert module.get_current_admin_unit_for_api() is None
