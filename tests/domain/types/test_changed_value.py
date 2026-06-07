import pytest
from pydantic import ValidationError

from project.domain.types.changed_value import ChangedValue


def test_changed_value_construction():
    cv = ChangedValue(old="old_val", new="new_val")
    assert cv.old == "old_val"
    assert cv.new == "new_val"


def test_changed_value_with_none_values():
    cv = ChangedValue(old=None, new=None)
    assert cv.old is None
    assert cv.new is None


def test_changed_value_with_int_values():
    cv = ChangedValue(old=1, new=2)
    assert cv.old == 1
    assert cv.new == 2


def test_changed_value_is_frozen():
    cv = ChangedValue(old="a", new="b")
    with pytest.raises(ValidationError):
        cv.old = "c"


def test_changed_value_frozen_new_field():
    cv = ChangedValue(old="a", new="b")
    with pytest.raises(ValidationError):
        cv.new = "d"
