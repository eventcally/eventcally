from typing import Optional

import pytest
from pydantic import ValidationError

from project.domain.types.changed_value import ChangedValue, OptionalChangedValue
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.unset import unset


class _SimpleModel(CustomBaseModel):
    name: str = "default"
    count: int = 0


class _MockEvent:
    """Simple event-like object to receive ChangedValue assignments."""

    pass


class _TypedEvent(CustomBaseModel):
    """Event with ChangedValue fields to test typed creation."""

    name: OptionalChangedValue[str] = None
    count: OptionalChangedValue[int] = None
    unrelated: Optional[str] = None


class _DictLike(dict):
    """Dict subclass used to test the isinstance(self, dict) branch."""

    pass


class TestUpdateFieldWithValueUnsetPath:
    def test_returns_false_when_new_value_is_unset(self):
        model = _SimpleModel(name="old")
        result = model._update_field_with_value("name", unset)
        assert result is False

    def test_field_unchanged_when_new_value_is_unset(self):
        model = _SimpleModel(name="original")
        model._update_field_with_value("name", unset)
        assert model.name == "original"


class TestUpdateFieldWithValueNoChangePath:
    def test_returns_false_when_value_unchanged(self):
        model = _SimpleModel(name="same")
        result = model._update_field_with_value("name", "same")
        assert result is False

    def test_field_stays_same(self):
        model = _SimpleModel(name="same")
        model._update_field_with_value("name", "same")
        assert model.name == "same"


class TestUpdateFieldWithValueChangedPath:
    def test_returns_true_when_value_changed(self):
        model = _SimpleModel(name="old")
        result = model._update_field_with_value("name", "new")
        assert result is True

    def test_field_updated_when_changed(self):
        model = _SimpleModel(name="old")
        model._update_field_with_value("name", "new")
        assert model.name == "new"

    def test_no_event_attribute_set_without_event(self):
        model = _SimpleModel(name="old")
        model._update_field_with_value("name", "new")
        # No event passed — no side effects on any event object


class TestUpdateFieldWithValueEventPath:
    def test_sets_changed_value_on_event(self):
        model = _SimpleModel(name="old")
        event = _MockEvent()
        result = model._update_field_with_value("name", "new", event)
        assert result is True
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "old"
        assert event.name.new == "new"

    def test_uses_field_name_as_event_attribute_by_default(self):
        model = _SimpleModel(count=5)
        event = _MockEvent()
        model._update_field_with_value("count", 10, event)
        assert hasattr(event, "count")
        assert event.count.old == 5
        assert event.count.new == 10

    def test_uses_event_field_name_override(self):
        model = _SimpleModel(name="old")
        event = _MockEvent()
        model._update_field_with_value("name", "new", event, "custom_name_field")
        assert hasattr(event, "custom_name_field")
        assert event.custom_name_field.old == "old"
        assert event.custom_name_field.new == "new"
        assert not hasattr(event, "name")


class TestUpdateFieldWithValueDictPath:
    def test_reads_value_via_get_for_dict(self):
        obj = _DictLike()
        obj["field"] = "old"
        result = CustomBaseModel._update_field_with_value(obj, "field", "new")
        assert result is True

    def test_updates_dict_key_instead_of_setattr(self):
        obj = _DictLike()
        obj["field"] = "old"
        CustomBaseModel._update_field_with_value(obj, "field", "new")
        assert obj["field"] == "new"

    def test_dict_returns_false_when_unchanged(self):
        obj = _DictLike()
        obj["field"] = "same"
        result = CustomBaseModel._update_field_with_value(obj, "field", "same")
        assert result is False


class TestUpdateFieldWithTypedChangedValue:
    def test_creates_typed_changed_value_for_str_field(self):
        model = _SimpleModel(name="old")
        event = _TypedEvent()
        model._update_field_with_value("name", "new", event)
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "old"
        assert event.name.new == "new"

    def test_creates_typed_changed_value_for_int_field(self):
        model = _SimpleModel(count=5)
        event = _TypedEvent()
        model._update_field_with_value("count", 10, event)
        assert isinstance(event.count, ChangedValue)
        assert event.count.old == 5
        assert event.count.new == 10

    def test_validates_str_type_on_changed_value(self):
        model = _SimpleModel(name="old")
        event = _TypedEvent()
        with pytest.raises(ValidationError):
            model._update_field_with_value("name", 123, event)

    def test_validates_int_type_on_changed_value(self):
        model = _SimpleModel(count=5)
        event = _TypedEvent()
        with pytest.raises(ValidationError):
            model._update_field_with_value("count", "not_an_int", event)

    def test_falls_back_for_non_pydantic_event(self):
        model = _SimpleModel(name="old")
        event = _MockEvent()
        model._update_field_with_value("name", "new", event)
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "old"
        assert event.name.new == "new"

    def test_falls_back_for_field_not_on_event(self):
        model = _SimpleModel(name="old")
        event = _MockEvent()
        model._update_field_with_value("name", "new", event, "nonexistent_field")
        assert isinstance(event.nonexistent_field, ChangedValue)
        assert event.nonexistent_field.old == "old"
        assert event.nonexistent_field.new == "new"

    def test_falls_back_for_non_changed_value_field(self):
        model = _SimpleModel(name="old")
        event = _TypedEvent()
        model._update_field_with_value("name", "new", event, "unrelated")
        assert isinstance(event.unrelated, ChangedValue)
        assert event.unrelated.old == "old"
        assert event.unrelated.new == "new"


class TestUpdateFieldWithValueCompareFn:
    def test_compare_fn_receiving_old_and_new(self):
        calls = []
        model = _SimpleModel(name="old")
        model._update_field_with_value(
            "name", "new", compare_fn=lambda o, n: (calls.append((o, n)), False)[1]
        )
        assert calls == [("old", "new")]

    def test_compare_fn_returning_true_skips_update(self):
        model = _SimpleModel(name="old")
        result = model._update_field_with_value(
            "name", "new", compare_fn=lambda o, n: True
        )
        assert result is False
        assert model.name == "old"

    def test_compare_fn_returning_false_performs_update(self):
        model = _SimpleModel(name="old")
        result = model._update_field_with_value(
            "name", "new", compare_fn=lambda o, n: False
        )
        assert result is True
        assert model.name == "new"

    def test_compare_fn_with_event(self):
        model = _SimpleModel(name="old")
        event = _MockEvent()
        model._update_field_with_value(
            "name", "new", event, compare_fn=lambda o, n: False
        )
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "old"
        assert event.name.new == "new"

    def test_compare_fn_returning_true_no_event_update(self):
        model = _SimpleModel(name="old")
        event = _MockEvent()
        model._update_field_with_value(
            "name", "new", event, compare_fn=lambda o, n: True
        )
        assert not hasattr(event, "name")
