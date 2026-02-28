from project.domain.types import ChangedValue, unset


class HasChangedValueMixin:
    def _has_set_changed_values(self) -> bool:
        for field_name in self.model_fields_set:
            # First check if the field's value is an instance of ChangedValue
            field_value = getattr(self, field_name)
            if isinstance(field_value, ChangedValue):
                return True

            # Check if the field has been set to a value other than unset
            if (
                self.model_fields[field_name].default is unset
                and field_value is not unset
            ):
                return True

        return False  # pragma: no cover
