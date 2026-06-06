from project.domain.types.changed_value import ChangedValue
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)
from project.domain.types.unset import unset
from project.domain.types.unset_field_factory import UnsetField


class _ModelWithUnsetField(CustomBaseModel):
    value: str = UnsetField()


class _ModelWithOptionalChangedValueField(CustomBaseModel):
    change: ChangedValue[str] = OptionalChangedValueField()


class TestUnsetField:
    def test_field_excluded_from_serialization_when_unset(self):
        model = _ModelWithUnsetField()
        data = model.model_dump()
        assert "value" not in data

    def test_field_included_in_serialization_when_set(self):
        model = _ModelWithUnsetField(value="hello")
        data = model.model_dump()
        assert data["value"] == "hello"

    def test_default_is_unset(self):
        model = _ModelWithUnsetField()
        assert model.value is unset


class TestOptionalChangedValueField:
    def test_field_excluded_when_none(self):
        model = _ModelWithOptionalChangedValueField()
        data = model.model_dump()
        assert "change" not in data

    def test_field_included_when_changed_value_set(self):
        cv = ChangedValue(old="a", new="b")
        model = _ModelWithOptionalChangedValueField(change=cv)
        data = model.model_dump()
        assert "change" in data
        assert data["change"]["old"] == "a"
        assert data["change"]["new"] == "b"

    def test_default_is_none(self):
        model = _ModelWithOptionalChangedValueField()
        assert model.change is None
