from typing import Any, Callable, Optional, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel

from project.domain.types.changed_value import ChangedValue


def _unwrap_optional(annotation):
    """Unwrap Optional[X] → X. Returns annotation unchanged if not Optional."""
    origin = get_origin(annotation)
    if origin is Union:
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    if origin is not None and hasattr(origin, "__value__"):
        value = origin.__value__
        value_origin = get_origin(value)
        if value_origin is Union:
            non_none = [a for a in get_args(value) if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
    return annotation


def _extract_changed_value_cls(model: BaseModel, field_name: str):
    """Extract the ChangedValue[T] class from a pydantic model's field annotation.

    Returns the concrete ChangedValue[T] class (e.g. ChangedValue[str]) so that
    pydantic validation is applied to old/new values, or None if the field is
    not typed as ChangedValue.
    """
    field_info = type(model).model_fields.get(field_name)
    if field_info is None:  # pragma: no cover
        return None

    annotation = _unwrap_optional(field_info.annotation)

    try:
        if issubclass(annotation, ChangedValue) and annotation is not ChangedValue:
            inner_type = annotation.model_fields["old"].annotation
            if isinstance(inner_type, TypeVar):
                type_args = get_args(field_info.annotation)
                if type_args and len(type_args) == 1:
                    inner_type = type_args[0]
            return ChangedValue[inner_type]
    except TypeError:
        pass

    return None


class CustomBaseModel(BaseModel):
    def validate_self(self) -> "CustomBaseModel":
        return self.model_validate(self.model_dump(round_trip=True), strict=True)

    def _update_field_with_value(
        self,
        field_name: str,
        new_value,
        event=None,
        event_field_name: Optional[str] = None,
        compare_fn: Optional[Callable[[Any, Any], bool]] = None,
    ) -> bool:
        from project.domain import types

        if new_value == types.unset:
            return False

        old_value = (
            self.get(field_name)
            if isinstance(self, dict)
            else getattr(self, field_name)
        )
        if compare_fn is not None:
            values_equal = compare_fn(old_value, new_value)
        else:
            values_equal = old_value == new_value
        if values_equal:
            return False

        if isinstance(self, dict):
            self[field_name] = new_value
        else:
            setattr(self, field_name, new_value)

        if event is not None:
            if event_field_name is None:
                event_field_name = field_name

            changed_value_cls = None
            if isinstance(event, BaseModel):
                changed_value_cls = _extract_changed_value_cls(event, event_field_name)

            if changed_value_cls is not None:
                changed_value = changed_value_cls(old=old_value, new=new_value)
            else:
                changed_value = types.ChangedValue(old=old_value, new=new_value)
            setattr(event, event_field_name, changed_value)

        return True
