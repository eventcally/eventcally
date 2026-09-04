import pytest


def test_handle_error_unique(app):
    from project.api import RestApi
    from project.utils import make_unique_violation

    error = make_unique_violation()

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Unique Violation"


def test_handle_error_checkViolation(app):
    from project.api import RestApi
    from project.utils import make_check_violation

    error = make_check_violation()

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Check Violation"


def test_handle_error_integrity(app):
    from project.api import RestApi
    from project.utils import make_integrity_error

    error = make_integrity_error("custom")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Integrity Error"


def test_handle_error_httpException(app):
    from werkzeug.exceptions import InternalServerError

    from project.api import RestApi

    error = InternalServerError()

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 500


def test_handle_error_domain_error(app):
    from project.api import RestApi
    from project.domain.errors import DuplicateError

    error = DuplicateError("Custom message")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Unique Violation"
    assert data["message"] == "Custom message"


def test_handle_error_unprocessableEntity(app):
    from marshmallow import ValidationError
    from werkzeug.exceptions import UnprocessableEntity

    from project.api import RestApi

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    error = UnprocessableEntity()
    error.exc = validation_error

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_validationError(app):
    from marshmallow import ValidationError

    from project.api import RestApi

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)
    (data, code) = api.handle_error(validation_error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_unspecificRaises(app):
    error = Exception()
    from project.api import RestApi

    app.config["PROPAGATE_EXCEPTIONS"] = False
    api = RestApi(app)

    with pytest.raises(Exception):
        api.handle_error(error)


def test_add_oauth2_scheme(app, utils):
    from project.api import add_oauth2_scheme_with_transport

    app.config["SERVER_NAME"] = "127.0.0.1"
    with app.app_context():
        add_oauth2_scheme_with_transport(False)


def test_init_api_event_lists_disabled():
    from project import create_app
    from project.api import EVENT_LIST_ENDPOINTS

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
            "FEATURE_EVENT_LISTS_ENABLED": False,
        }
    )

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert endpoints.isdisjoint(EVENT_LIST_ENDPOINTS)
    assert "api_v1_organization_event_list" in endpoints


def test_init_api_event_lists_enabled():
    from project import create_app
    from project.api import EVENT_LIST_ENDPOINTS

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
            "FEATURE_EVENT_LISTS_ENABLED": True,
        }
    )

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert EVENT_LIST_ENDPOINTS.issubset(endpoints)
    assert "api_v1_organization_event_list" in endpoints


def test_init_api_event_lists_disabled_via_feature_flags_env(monkeypatch):
    from project import create_app
    from project.api import EVENT_LIST_ENDPOINTS

    monkeypatch.setenv("FEATURE_FLAGS", "EventListsDisabled")

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
        }
    )

    assert app.config["FEATURE_EVENT_LISTS_ENABLED"] is False
    assert app.config["FEATURE_FLAGS"] == {"EventListsDisabled"}

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert endpoints.isdisjoint(EVENT_LIST_ENDPOINTS)
    assert "api_v1_organization_event_list" in endpoints


def test_init_api_user_favorites_disabled():
    from project import create_app
    from project.api import USER_FAVORITE_ENDPOINTS

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
            "FEATURE_USER_FAVORITES_ENABLED": False,
        }
    )

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert endpoints.isdisjoint(USER_FAVORITE_ENDPOINTS)
    assert "api_v1_user_organization_membership_list" in endpoints


# (endpoint set in project.api, derived config key, FEATURE_FLAGS token)
UNUSED_API_ENDPOINT_FLAGS = [
    (
        "API_EVENT_DATE_ENDPOINTS",
        "FEATURE_API_EVENT_DATE_ENABLED",
        "ApiEventDateDisabled",
    ),
    (
        "API_EVENT_DATES_ENDPOINTS",
        "FEATURE_API_EVENT_DATES_ENABLED",
        "ApiEventDatesDisabled",
    ),
    (
        "API_EVENT_LIST_ENDPOINTS",
        "FEATURE_API_EVENT_LIST_ENABLED",
        "ApiEventListDisabled",
    ),
]


def _endpoint_set(name):
    import project.api

    return getattr(project.api, name)


@pytest.mark.parametrize(
    "endpoint_set_name, config_key, token", UNUSED_API_ENDPOINT_FLAGS
)
def test_init_api_unused_endpoints_disabled(endpoint_set_name, config_key, token):
    from project import create_app

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
            config_key: False,
        }
    )

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert endpoints.isdisjoint(_endpoint_set(endpoint_set_name))
    assert "api_v1_event_search" in endpoints


@pytest.mark.parametrize(
    "endpoint_set_name, config_key, token", UNUSED_API_ENDPOINT_FLAGS
)
def test_init_api_unused_endpoints_enabled_by_default(
    endpoint_set_name, config_key, token
):
    from project import create_app

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
        }
    )

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert app.config[config_key] is True
    assert _endpoint_set(endpoint_set_name).issubset(endpoints)


@pytest.mark.parametrize(
    "endpoint_set_name, config_key, token", UNUSED_API_ENDPOINT_FLAGS
)
def test_init_api_unused_endpoints_disabled_via_feature_flags_env(
    endpoint_set_name, config_key, token, monkeypatch
):
    from project import create_app

    monkeypatch.setenv("FEATURE_FLAGS", token)

    app = create_app(
        {
            "TESTING": True,
            "SERVER_NAME": "localhost",
        }
    )

    assert app.config[config_key] is False
    assert app.config["FEATURE_FLAGS"] == {token}

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert endpoints.isdisjoint(_endpoint_set(endpoint_set_name))
    assert "api_v1_event_search" in endpoints
