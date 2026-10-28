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


# Deprecated routes: documented as `deprecated`, hidden by ApiDeprecatedEndpointsDisabled.


def _app_with_deprecated_endpoints(shown: bool):
    from project.factory import create_app

    return create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
            "FEATURE_API_DEPRECATED_ENDPOINTS_ENABLED": shown,
        }
    )


def _deprecated_entries():
    from project.presentation.api import resource_registry

    return {
        endpoint: (url, deprecated, deprecated_methods)
        for endpoint, (
            _resource,
            url,
            _docs,
            deprecated,
            deprecated_methods,
        ) in resource_registry.items()
        if deprecated
    }


def _swagger_paths(app):
    return app.test_client().get("/swagger/").json["paths"]


def _swagger_path(url):
    import re

    return "/api/v1" + re.sub(r"<(?:int:)?(\w+)>", r"{\1}", url)


def _rules(app, endpoint):
    return [rule for rule in app.url_map.iter_rules() if rule.endpoint == endpoint]


def test_deprecated_endpoints_are_registered_and_documented_by_default():
    app = _app_with_deprecated_endpoints(True)
    entries = _deprecated_entries()
    paths = _swagger_paths(app)

    assert len(entries) >= 20
    for endpoint, (url, replacement, methods) in entries.items():
        assert _rules(app, endpoint)
        operations = {
            method: operation
            for method, operation in paths[_swagger_path(url)].items()
            if method in ("get", "put", "post", "patch", "delete")
        }
        for method, operation in operations.items():
            if methods is None or method in methods:
                assert operation["deprecated"] is True
                assert replacement in operation["description"]
            else:
                assert "deprecated" not in operation


def test_replacements_are_not_deprecated():
    app = _app_with_deprecated_endpoints(True)
    paths = _swagger_paths(app)

    for path in (
        "/api/v1/organizations/{id}/outgoing-event-reference-requests",
        "/api/v1/organizations/{id}/incoming-event-reference-requests/{event_reference_request_id}",
        "/api/v1/organizations/{id}/events/{event_id}",
        "/api/v1/organizations/{id}/outgoing-organization-relations/by-target/{target_id}",
        "/api/v1/organizations/{id}/organization-invitations",
    ):
        operations = [
            operation
            for method, operation in paths[path].items()
            if method in ("get", "put", "post", "patch", "delete")
        ]
        assert operations
        assert all("deprecated" not in operation for operation in operations)

    # Only the writes of /events/<id> are deprecated, the public read stays.
    assert "deprecated" not in paths["/api/v1/events/{id}"]["get"]
    assert paths["/api/v1/events/{id}"]["put"]["deprecated"] is True


def test_deprecated_endpoints_are_hidden_with_the_flag():
    app = _app_with_deprecated_endpoints(False)
    paths = _swagger_paths(app)

    for endpoint, (url, _replacement, methods) in _deprecated_entries().items():
        if not methods:
            assert not _rules(app, endpoint)
            assert _swagger_path(url) not in paths
            continue

        (rule,) = _rules(app, endpoint)
        assert rule.methods.isdisjoint({method.upper() for method in methods})
        assert {"GET", "HEAD", "OPTIONS"} >= rule.methods
        assert set(paths[_swagger_path(url)]).isdisjoint(methods)
        assert "get" in paths[_swagger_path(url)]

    # Every replacement stays.
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "api_v1_organization_incoming_event_reference_request" in endpoints
    assert "api_v1_organization_event" in endpoints
    assert "api_v1_organization_outgoing_organization_relation_by_target" in endpoints
    assert "api_v1_event" in endpoints
    assert "api_v1_event_reference_request" not in endpoints


def test_hidden_deprecated_method_answers_405():
    app = _app_with_deprecated_endpoints(False)
    client = app.test_client()

    for method in ("put", "patch", "delete"):
        for resource in ("events", "places", "organizers"):
            response = getattr(client, method)(f"/api/v1/{resource}/1")
            assert response.status_code == 405

    assert client.post("/api/v1/event-reference-requests/1/verify").status_code == 404


def test_deprecated_endpoints_are_hidden_via_feature_flags_env(monkeypatch):
    from project.factory import create_app

    monkeypatch.setenv("FEATURE_FLAGS", "ApiDeprecatedEndpointsDisabled")

    app = create_app({"TESTING": True, "SERVER_NAME": "localhost"})

    assert app.config["FEATURE_API_DEPRECATED_ENDPOINTS_ENABLED"] is False
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "api_v1_organization_relation" not in endpoints
    assert "api_v1_organization_outgoing_organization_relation" in endpoints


def test_hiding_does_not_leak_between_apps():
    hidden = _app_with_deprecated_endpoints(False)
    shown = _app_with_deprecated_endpoints(True)

    assert not _rules(hidden, "api_v1_organization_relation")
    assert _rules(shown, "api_v1_organization_relation")
    assert {"PUT", "PATCH", "DELETE"} <= _rules(shown, "api_v1_event")[0].methods
    assert not {"PUT", "PATCH", "DELETE"} & _rules(hidden, "api_v1_event")[0].methods
