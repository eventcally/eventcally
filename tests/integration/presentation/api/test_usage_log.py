import json
import logging

import pytest
import sqlalchemy

from tests.integration.presentation.api.test_app_webhook import _setup_app_auth
from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


class _CollectingHandler(logging.Handler):
    """Keeps the lines as the JSON formatter of production renders them."""

    def __init__(self):
        from project.infrastructure.logging_config import build_formatter

        super().__init__()
        self.setFormatter(build_formatter("json"))
        self.lines = []

    def emit(self, record):
        self.lines.append(self.format(record))


@pytest.fixture
def usage_lines():
    from project.infrastructure.logging_config import API_USAGE_LOGGER

    handler = _CollectingHandler()
    logger = logging.getLogger(API_USAGE_LOGGER)
    logger.addHandler(handler)
    yield handler.lines
    logger.removeHandler(handler)


def _records(lines):
    return [json.loads(line) for line in lines]


def _single_record(lines):
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["type"] == "api_usage"
    assert record["event"] == "api_usage"
    assert record["logger"] == "eventcally.api_usage"
    return record


def _reset_limiter(app):
    from project.infrastructure.extensions import limiter

    with app.app_context():
        limiter.reset()


def _token(app, access_token):
    from project.infrastructure.models import OAuth2Token

    with app.app_context():
        token = OAuth2Token.query.filter(
            OAuth2Token.access_token == access_token
        ).first()
        return {
            "id": token.id,
            "client_id": token.client_id,
            "client_admin_unit_id": token.client.admin_unit_id,
        }


def _assert_no_secret(lines, *secrets):
    for line in lines:
        for secret in secrets:
            assert secret not in line


def test_api_key(client, app, seeder: Seeder, utils: UtilActions, usage_lines):
    user_id, admin_unit_id = seeder.setup_api_access(
        user_access=False, use_api_key=True
    )

    response = utils.get_json_ok(utils.get_url("api_v1_license_list"))

    record = _single_record(usage_lines)
    assert record["auth"] == "api_key"
    assert record["api_key_id"]
    assert record["user_id"] == user_id
    assert record["admin_unit_id"] is None
    assert record["token_id"] is None
    assert record["client_id"] is None
    assert record["rate_limit_key"] == f"apikey-{record['api_key_id']}"
    assert record["status"] == 200
    assert record["level"] == "info"
    assert record["method"] == "GET"
    assert record["endpoint"] == "api_v1_license_list"
    assert record["path"] == "/api/v1/licenses"
    assert record["timestamp"].endswith("Z")
    assert isinstance(record["duration_ms"], int)
    assert record["ip"] == "127.0.0.1"
    assert record["request_id"] == response.headers["X-Request-ID"]
    _assert_no_secret(usage_lines, utils._api_key)


def test_api_key_of_organization(client, app, seeder: Seeder, utils, usage_lines):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    _, key = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    utils.setup_api_key(key)

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    record = _single_record(usage_lines)
    assert record["auth"] == "api_key"
    assert record["admin_unit_id"] == admin_unit_id
    assert record["user_id"] is None


def test_user_token(client, app, seeder: Seeder, utils: UtilActions, usage_lines):
    user_id, admin_unit_id = seeder.setup_api_access()
    token = _token(app, utils._access_token)

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    record = _single_record(usage_lines)
    assert record["auth"] == "oauth2"
    assert record["token_id"] == token["id"]
    assert record["client_id"] == token["client_id"]
    assert record["user_id"] == user_id
    assert record["app_id"] is None
    assert record["app_installation_id"] is None
    assert record["api_key_id"] is None
    assert record["admin_unit_id"] == token["client_admin_unit_id"]
    assert record["rate_limit_key"].endswith(f"-{user_id}")
    _assert_no_secret(usage_lines, utils._access_token)


def test_client_credentials_token(client, app, seeder: Seeder, utils, usage_lines):
    seeder.setup_api_access(user_access=False)
    token = _token(app, utils._access_token)

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    record = _single_record(usage_lines)
    assert record["auth"] == "oauth2"
    assert record["token_id"] == token["id"]
    assert record["user_id"] is None


def test_app_token(client, app, db, seeder: Seeder, utils: UtilActions, usage_lines):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    oauth2_client_id = _setup_app_auth(seeder, utils, app, db, admin_unit_id)
    usage_lines.clear()  # the token endpoint is not part of the API

    utils.get_json_ok(utils.get_url("api_v1_app_webhook_delivery_list"))

    record = _single_record(usage_lines)
    assert record["auth"] == "oauth2"
    assert record["app_id"] == oauth2_client_id
    assert record["app_installation_id"] is None
    assert record["user_id"] is None
    assert record["admin_unit_id"] == admin_unit_id
    _assert_no_secret(usage_lines, utils._access_token)


def test_app_installation_token(client, app, seeder: Seeder, utils, usage_lines):
    from project.infrastructure.models import AppInstallation

    _, admin_unit_id = seeder.setup_api_access(as_app_installation=True)
    with app.app_context():
        app_installation = AppInstallation.query.first()
        app_installation_id = app_installation.id
        app_id = app_installation.oauth2_client_id

    url = utils.get_url(
        "api_v1_organization_organization_invitation_list", id=admin_unit_id
    )
    utils.get_json_ok(url)

    record = _single_record(usage_lines)
    assert record["auth"] == "oauth2"
    assert record["app_installation_id"] == app_installation_id
    assert record["app_id"] == app_id
    assert record["user_id"] is None
    assert record["admin_unit_id"] == admin_unit_id
    assert record["endpoint"] == "api_v1_organization_organization_invitation_list"
    assert (
        record["path"]
        == f"/api/v1/organizations/{admin_unit_id}/organization-invitations"
    )
    _assert_no_secret(usage_lines, utils._access_token)


def test_unauthorized_after_authentication(client, app, db, seeder, utils, usage_lines):
    _, admin_unit_id = seeder.setup_api_access(as_app_installation=True)
    with app.app_context():
        from project.infrastructure.models import AppInstallation

        for app_installation in AppInstallation.query.all():
            app_installation.permissions = []
        db.session.commit()

    url = utils.get_url(
        "api_v1_organization_organization_invitation_list", id=admin_unit_id
    )
    utils.assert_response_unauthorized(utils.get_json(url))

    record = _single_record(usage_lines)
    assert record["status"] == 401
    assert record["auth"] == "oauth2"
    assert record["app_installation_id"]
    assert record["admin_unit_id"] == admin_unit_id


@pytest.mark.parametrize(
    "headers, auth",
    [
        ({"Authorization": "Bearer invalid-token"}, "oauth2"),
        ({"X-API-Key": "invalid-key"}, "api_key"),
        ({}, "none"),
    ],
)
def test_failed_authentication(client, app, utils, usage_lines, headers, auth):
    response = utils.get_json(utils.get_url("api_v1_license_list"), headers=headers)
    assert response.status_code == 401

    record = _single_record(usage_lines)
    assert record["status"] == 401
    assert record["auth"] == auth
    assert record["token_id"] is None
    assert record["api_key_id"] is None
    assert record["rate_limit_key"] is None
    _assert_no_secret(usage_lines, "invalid-token", "invalid-key")


def test_rate_limited(client, app, db, seeder: Seeder, utils, usage_lines):
    from project.infrastructure.models import ApiKey

    seeder.setup_api_access(user_access=False, use_api_key=True)
    with app.app_context():
        ApiKey.query.first().rate_limit_value = "1/minute"
        db.session.commit()
    _reset_limiter(app)

    url = utils.get_url("api_v1_license_list")
    statuses = [utils.get_json(url).status_code for _ in range(2)]

    assert statuses == [200, 429]
    record = _records(usage_lines)[-1]
    assert record["status"] == 429
    assert record["auth"] == "api_key"
    assert record["api_key_id"]


def test_anonymous(client, app, utils, usage_lines):
    app.config["API_READ_ANONYM"] = True
    _reset_limiter(app)

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    record = _single_record(usage_lines)
    assert record["auth"] == "none"
    assert record["rate_limit_key"] == "127.0.0.1"


def test_switched_off(client, app, seeder: Seeder, utils, usage_lines):
    seeder.setup_api_access()
    app.config["API_USAGE_LOG"] = False

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    assert usage_lines == []


def test_only_api_requests(client, app, utils, usage_lines):
    utils.get_ok(utils.get_url("main.home"))

    assert usage_lines == []


def test_never_raises(client, app, seeder: Seeder, utils, usage_lines, mocker):
    from project.presentation.api import usage_log

    seeder.setup_api_access()
    mocker.patch.object(
        usage_log, "build_api_usage_record", side_effect=RuntimeError("boom")
    )
    exception = mocker.patch.object(usage_log.logger, "exception")

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    assert usage_lines == []
    exception.assert_called_once_with("Could not write the API usage record")


def test_secret_query_arguments_are_redacted(client, app, seeder, utils, usage_lines):
    seeder.setup_api_access(user_access=False, use_api_key=True)
    url = utils.get_url("api_v1_license_list")

    utils.get_json_ok(f"{url}?access_token=SECRET1&API_KEY=SECRET2&x=2&x=3")

    record = _single_record(usage_lines)
    assert record["path"] == (
        "/api/v1/licenses?access_token=%5Bredacted%5D&API_KEY=%5Bredacted%5D" "&x=2&x=3"
    )
    _assert_no_secret(usage_lines, "SECRET1", "SECRET2")


def test_long_values_are_truncated(client, app, seeder, utils, usage_lines):
    from project.presentation.api.usage_log import (
        MAX_PATH_LENGTH,
        MAX_USER_AGENT_LENGTH,
    )

    seeder.setup_api_access(user_access=False, use_api_key=True)
    url = utils.get_url("api_v1_license_list")

    utils.get_json_ok(f"{url}?q={'x' * 3000}", headers={"User-Agent": "a" * 1000})

    record = _single_record(usage_lines)
    assert len(record["path"]) == MAX_PATH_LENGTH
    assert len(record["user_agent"]) == MAX_USER_AGENT_LENGTH


def test_incoming_request_id(client, app, seeder, utils, usage_lines):
    seeder.setup_api_access(user_access=False, use_api_key=True)

    response = utils.get_json_ok(
        utils.get_url("api_v1_license_list"), headers={"X-Request-ID": "abc-123"}
    )

    assert response.headers["X-Request-ID"] == "abc-123"
    assert _single_record(usage_lines)["request_id"] == "abc-123"


def test_propagated_exception_is_recorded_once_as_500(usage_lines):
    from project.factory import create_app

    test_app = create_app({"TESTING": True, "PROPAGATE_EXCEPTIONS": True})

    def boom():
        raise RuntimeError("boom")

    test_app.add_url_rule("/api/v1/boom", "boom", boom)

    with pytest.raises(RuntimeError):
        test_app.test_client().get("/api/v1/boom")

    record = _single_record(usage_lines)
    assert record["status"] == 500
    assert record["level"] == "error"
    assert record["endpoint"] == "boom"
    assert record["auth"] == "none"
    assert record["duration_ms"] is not None


def _count_queries(app, utils, url):
    count = 0

    def _count(*args, **kwargs):
        nonlocal count
        count += 1

    sqlalchemy.event.listen(sqlalchemy.engine.Engine, "before_cursor_execute", _count)
    try:
        utils.get_json_ok(url)
    finally:
        sqlalchemy.event.remove(
            sqlalchemy.engine.Engine, "before_cursor_execute", _count
        )
    return count


@pytest.mark.parametrize("credential", ["api_key", "user_token", "app_installation"])
def test_no_extra_queries(client, app, seeder, utils, usage_lines, credential):
    """The record reads what authentication already loaded."""
    if credential == "app_installation":
        _, admin_unit_id = seeder.setup_api_access(as_app_installation=True)
        url = utils.get_url(
            "api_v1_organization_organization_invitation_list", id=admin_unit_id
        )
    else:
        seeder.setup_api_access(
            user_access=credential == "user_token",
            use_api_key=credential == "api_key",
        )
        url = utils.get_url("api_v1_license_list")
    utils.get_json_ok(url)  # warm up

    app.config["API_USAGE_LOG"] = False
    without_log = _count_queries(app, utils, url)
    app.config["API_USAGE_LOG"] = True
    with_log = _count_queries(app, utils, url)

    assert with_log == without_log
    assert json.loads(usage_lines[-1])["type"] == "api_usage"


def test_remembering_never_raises(client, app, seeder, utils, usage_lines, mocker):
    from project.presentation.api import usage_log

    seeder.setup_api_access(user_access=False, use_api_key=True)
    mocker.patch.object(usage_log, "ApiUsageAuth", side_effect=RuntimeError("boom"))
    exception = mocker.patch.object(usage_log.logger, "exception")

    utils.get_json_ok(utils.get_url("api_v1_license_list"))

    exception.assert_any_call("Could not remember the API usage auth")
