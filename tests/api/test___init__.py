import pytest
from project.api import RestApi


class Psycog2Error(object):
    def __init__(self, pgcode):
        self.pgcode = pgcode


def test_handle_error_unique(app):
    from sqlalchemy.exc import IntegrityError
    from psycopg2.errorcodes import UNIQUE_VIOLATION

    orig = Psycog2Error(UNIQUE_VIOLATION)
    error = IntegrityError("Select", list(), orig)

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 400
    assert data["name"] == "Unique Violation"


def test_handle_error_httpException(app):
    from werkzeug.exceptions import InternalServerError

    error = InternalServerError()

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 500


def test_handle_error_unprocessableEntity(app):
    from werkzeug.exceptions import UnprocessableEntity
    from marshmallow import ValidationError

    args = {"name": ["Required"]}
    validation_error = ValidationError(args)

    error = UnprocessableEntity()
    error.exc = validation_error

    api = RestApi(app)
    (data, code) = api.handle_error(error)
    assert code == 422
    assert data["errors"][0]["field"] == "name"
    assert data["errors"][0]["message"] == "Required"


def test_handle_error_unspecificRaises(app):
    error = Exception()
    api = RestApi(app)

    with pytest.raises(Exception):
        api.handle_error(error)
