import pytest

from project.api import RestApi


def test_handle_error_unique(app):
    from project.utils import make_unique_violation

    error = make_unique_violation()

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Unique Violation"


def test_handle_error_checkViolation(app):
    from project.utils import make_check_violation

    error = make_check_violation()

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Check Violation"


def test_handle_error_integrity(app):
    from project.utils import make_integrity_error

    error = make_integrity_error("custom")

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Integrity Error"


def test_handle_error_httpException(app):
    from werkzeug.exceptions import InternalServerError

    error = InternalServerError()

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 500


def test_handle_error_unprocessableEntity(app):
    from marshmallow import ValidationError
    from werkzeug.exceptions import UnprocessableEntity

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    error = UnprocessableEntity()
    error.exc = validation_error

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_validationError(app):
    from marshmallow import ValidationError

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    api = RestApi(app)
    (data, code) = api.handle_error(validation_error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_unspecificRaises(app):
    error = Exception()
    api = RestApi(app)

    with pytest.raises(Exception):
        api.handle_error(error)


def test_add_oauth2_scheme(app, utils):
    from project.api import add_oauth2_scheme_with_transport

    app.config["SERVER_NAME"] = "127.0.0.1"
    with app.app_context():
        add_oauth2_scheme_with_transport(False)
