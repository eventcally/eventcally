import json
import os
import subprocess
import sys

import pytest


def test_handle_error_unique(app):
    from project.presentation.api import RestApi
    from project.shared.utils import make_unique_violation

    error = make_unique_violation()

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Unique Violation"


def test_handle_error_checkViolation(app):
    from project.presentation.api import RestApi
    from project.shared.utils import make_check_violation

    error = make_check_violation()

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Check Violation"


def test_handle_error_integrity(app):
    from project.presentation.api import RestApi
    from project.shared.utils import make_integrity_error

    error = make_integrity_error("custom")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Integrity Error"


def test_handle_error_httpException(app):
    from werkzeug.exceptions import InternalServerError

    from project.presentation.api import RestApi

    error = InternalServerError()

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 500


def test_handle_error_domain_error(app):
    from project.domain.errors import DuplicateError
    from project.presentation.api import RestApi

    error = DuplicateError("Custom message")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Unique Violation"
    assert data["message"] == "Custom message"


def test_handle_error_unauthorized(app):
    from project.domain.errors import UnauthorizedError
    from project.presentation.api import RestApi

    error = UnauthorizedError("Custom message")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 401
    assert data["name"] == "Unauthorized"
    assert data["message"] == "Custom message"


def test_handle_error_unprocessableEntity(app):
    from marshmallow import ValidationError
    from werkzeug.exceptions import UnprocessableEntity

    from project.presentation.api import RestApi

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    error = UnprocessableEntity()
    error.exc = validation_error

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_validationError(app):
    from marshmallow import ValidationError

    from project.presentation.api import RestApi

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    data, code = api.handle_error(validation_error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_unspecificRaises(app):
    error = Exception()
    from project.presentation.api import RestApi

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)

    with pytest.raises(Exception):
        api.handle_error(error)


def test_add_oauth2_scheme(app, utils):
    from project.presentation.api import add_oauth2_scheme_with_transport

    app.config["SERVER_NAME"] = "127.0.0.1"
    with app.app_context():
        add_oauth2_scheme_with_transport(False)


def test_init_api_registers_event_date_endpoint():
    from project.factory import create_app

    app = create_app({"TESTING": True, "SERVER_NAME": "localhost"})

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert "api_v1_event_date" in endpoints
    assert "api_v1_event_search" in endpoints
    assert "api_v1_event_list" not in endpoints
    assert "api_v1_event_dates" not in endpoints


def test_init_api_ignores_retired_event_date_flag(monkeypatch):
    from project.factory import create_app

    monkeypatch.setenv("FEATURE_FLAGS", "ApiEventDateDisabled")

    app = create_app({"TESTING": True, "SERVER_NAME": "localhost"})

    assert app.config["FEATURE_FLAGS"] == set()
    assert "FEATURE_API_EVENT_DATE_ENABLED" not in app.config

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert "api_v1_event_date" in endpoints


_API_RULES_OF_A_FRESH_APP = """
import json
from project.factory import create_app

app = create_app({"SERVER_NAME": "localhost"})
print(json.dumps(sorted(
    [rule.endpoint, rule.rule]
    for rule in app.url_map.iter_rules()
    if rule.rule.startswith("/api/v1/")
)))
"""


def _api_rules(app):
    return sorted(
        [rule.endpoint, rule.rule]
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/v1/")
    )


def test_create_app_registers_every_api_resource(app):
    # A fresh interpreter: there the conftest has not imported every module of
    # project.presentation.api, so only the imports in init_api() fill the registry.
    result = subprocess.run(
        [sys.executable, "-c", _API_RULES_OF_A_FRESH_APP],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"stderr={result.stderr}"

    fresh = json.loads(result.stdout.strip().splitlines()[-1])
    assert fresh == _api_rules(app)
    assert [
        "api_v1_user_organization_invitation_list",
        "/api/v1/user/organization-invitations",
    ] in fresh
