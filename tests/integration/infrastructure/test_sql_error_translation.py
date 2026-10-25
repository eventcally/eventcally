import pytest
from sqlalchemy.exc import SQLAlchemyError

from project.domain.errors import ConstraintError, DuplicateError, InfrastructureError
from project.infrastructure.sql_error_translation import (
    flush,
    raise_domain_error_from_sql_error,
)


class _Orig(Exception):
    def __init__(self, pgcode):
        self.pgcode = pgcode


def _sql_error(pgcode):
    error = SQLAlchemyError()
    error.orig = _Orig(pgcode)
    return error


@pytest.mark.parametrize(
    "pgcode,expected",
    [
        ("23505", DuplicateError),
        ("23514", ConstraintError),
        ("40001", InfrastructureError),
    ],
)
def test_pgcode_maps_to_domain_error(pgcode, expected):
    error = _sql_error(pgcode)

    with pytest.raises(expected) as excinfo:
        raise_domain_error_from_sql_error(error)

    assert excinfo.value.cause is error


def test_error_without_pgcode_is_an_infrastructure_error():
    with pytest.raises(InfrastructureError):
        raise_domain_error_from_sql_error(SQLAlchemyError())


def test_flush_translates_sql_errors(mocker):
    session = mocker.Mock()
    session.flush.side_effect = _sql_error("23505")

    with pytest.raises(DuplicateError):
        flush(session)


def test_flush_passes_when_the_session_flushes(mocker):
    session = mocker.Mock()

    flush(session)

    session.flush.assert_called_once_with()
