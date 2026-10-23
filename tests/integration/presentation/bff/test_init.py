import pytest
from flask_wtf.csrf import CSRFError

from project.domain.errors import BaseError
from project.presentation.bff import (
    _handle_base_error,
    _handle_csrf_error,
    _handle_http_exception,
    _protect_unsafe_methods,
)


def test_unsafe_method_without_csrf_token(app):
    with app.test_request_context("/bff/admin/users", method="POST"):
        with pytest.raises(CSRFError) as exc:
            _protect_unsafe_methods()

        response, code = _handle_csrf_error(exc.value)

    assert code == 400
    assert response.json["message"]


def test_safe_method_skips_csrf(app):
    with app.test_request_context("/bff/admin/users", method="GET"):
        assert _protect_unsafe_methods() is None


def test_base_error_is_400(app):
    with app.test_request_context("/bff/admin/users"):
        response, code = _handle_base_error(BaseError("Nope"))

    assert code == 400
    assert response.json["message"] == "Nope"


def test_http_exception_keeps_code(app):
    from werkzeug.exceptions import Conflict

    with app.test_request_context("/bff/admin/users"):
        response, code = _handle_http_exception(Conflict())

    assert code == 409
    assert response.json["name"] == "Conflict"


def test_anonymous_gets_json_401_without_accept_header(client):
    response = client.get("/bff/admin/users")

    assert response.status_code == 401
    assert response.json["name"] == "Unauthorized"


def test_unauthorized_error_maps_to_401_or_403(app, seeder, utils):
    from project.domain.errors.unauthorized_error import UnauthorizedError
    from project.presentation.bff import _handle_unauthorized_error

    with app.test_request_context("/bff/admin/users"):
        _, code = _handle_unauthorized_error(UnauthorizedError("no"))
    assert code == 401

    seeder.create_user()
    utils.login()
    with app.test_request_context("/bff/admin/users"):
        from flask_login import login_user

        from project.infrastructure.extensions import db
        from project.infrastructure.models import User

        login_user(db.session.query(User).first())
        _, code = _handle_unauthorized_error(UnauthorizedError("no"))
    assert code == 403


def test_integrity_error_maps_to_400(app):
    from sqlalchemy.exc import IntegrityError

    from project.presentation.bff import _handle_integrity_error

    with app.test_request_context("/bff/admin/users"):
        _, code = _handle_integrity_error(IntegrityError("s", {}, Exception()))
    assert code == 400


def test_field_validation_error_is_422(app):
    from project.presentation.bff import _handle_field_validation_error
    from project.presentation.bff.errors import FieldValidationError

    with app.test_request_context("/bff/admin/users"):
        response, code = _handle_field_validation_error(
            FieldValidationError(["email"], "Does not match")
        )

    assert code == 422
    assert response.json["name"] == "Unprocessable Entity"
    assert response.json["errors"] == [{"loc": ["email"], "msg": "Does not match"}]


def test_field_validation_error_reports_several_fields(app):
    from project.presentation.bff import _handle_field_validation_error
    from project.presentation.bff.errors import FieldValidationError

    with app.test_request_context("/bff/admin/users"):
        response, code = _handle_field_validation_error(
            FieldValidationError(
                errors=[(["name"], "Taken"), (["short_name"], "Taken")]
            )
        )

    assert code == 422
    assert response.json["errors"] == [
        {"loc": ["name"], "msg": "Taken"},
        {"loc": ["short_name"], "msg": "Taken"},
    ]


def test_public_blueprint_is_open_to_anonymous(client, seeder):
    seeder.setup_base(log_in=False)

    response = client.get("/bff/public/events/4711/report-form")

    # Not the 401 of the session check: the event just does not exist.
    assert response.status_code == 404
