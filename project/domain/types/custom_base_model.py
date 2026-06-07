from typing import Optional

from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    def _update_field_with_value(
        self,
        field_name: str,
        new_value,
        event=None,
        event_field_name: Optional[str] = None,
    ) -> bool:
        from project.domain import types

        if new_value == types.unset:
            return False

        old_value = (
            self.get(field_name)
            if isinstance(self, dict)
            else getattr(self, field_name)
        )
        if old_value == new_value:
            return False

        if isinstance(self, dict):
            self[field_name] = new_value
        else:
            setattr(self, field_name, new_value)

        if event is not None:
            if event_field_name is None:
                event_field_name = field_name

            changed_value = types.ChangedValue(old=old_value, new=new_value)
            setattr(event, event_field_name, changed_value)

        return True
