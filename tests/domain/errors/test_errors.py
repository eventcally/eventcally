import pytest

from project.domain.errors.base_error import BaseError
from project.domain.errors.constraint_error import ConstraintError
from project.domain.errors.duplicate_error import DuplicateError
from project.domain.errors.infrastructure_error import InfrastructureError
from project.domain.errors.not_found_error import NotFoundError


class TestBaseError:
    def test_default_message_used_when_no_message_given(self):
        error = BaseError()
        assert error.message == "An error occurred"

    def test_custom_message_used_when_provided(self):
        error = BaseError(message="custom message")
        assert error.message == "custom message"

    def test_cause_stored(self):
        cause = ValueError("root cause")
        error = BaseError(cause=cause)
        assert error.cause is cause

    def test_cause_is_none_by_default(self):
        error = BaseError()
        assert error.cause is None

    def test_is_exception(self):
        assert isinstance(BaseError(), Exception)

    def test_exception_args_contain_message(self):
        error = BaseError(message="oops")
        assert str(error) == "oops"


class TestConstraintError:
    def test_default_message(self):
        error = ConstraintError()
        assert "constraint" in error.message.lower()

    def test_is_base_error(self):
        assert isinstance(ConstraintError(), BaseError)

    def test_custom_message(self):
        error = ConstraintError(message="custom")
        assert error.message == "custom"


class TestDuplicateError:
    def test_default_message(self):
        error = DuplicateError()
        assert (
            "duplicate" in error.message.lower()
            or "already exists" in error.message.lower()
        )

    def test_is_base_error(self):
        assert isinstance(DuplicateError(), BaseError)


class TestInfrastructureError:
    def test_default_message(self):
        error = InfrastructureError()
        assert "infrastructure" in error.message.lower()

    def test_is_base_error(self):
        assert isinstance(InfrastructureError(), BaseError)


class TestNotFoundError:
    def test_default_message(self):
        error = NotFoundError()
        assert "not found" in error.message.lower()

    def test_is_base_error(self):
        assert isinstance(NotFoundError(), BaseError)

    def test_raise_and_catch_as_exception(self):
        with pytest.raises(NotFoundError):
            raise NotFoundError()
