from project.domain.types import ChangedValue


class HasChangedValueMixin:
    def _has_set_changed_values(self) -> bool:
        for field_name in self.model_fields_set:
            if isinstance(getattr(self, field_name), ChangedValue):
                return True

        return False
