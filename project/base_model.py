from typing import List, Optional

from flask_babel import gettext
from flask_sqlalchemy.model import Model as SQLAlchemyModel

from project.domain import commands, events, types
from project.utils import (
    class_name_to_model_name,
    model_name_to_plural,
    snake_case_to_human,
)


class CustomModel(SQLAlchemyModel):
    # __model_name__ = None
    # __model_name_plural__ = None
    # __display_name__ = None
    # __display_name_plural__ = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not cls.__dict__.get("__abstract__", False):
            if not getattr(cls, "__model_name__", None):
                cls.__model_name__ = class_name_to_model_name(cls.__name__)

            if not getattr(cls, "__model_name_plural__", None):
                cls.__model_name_plural__ = model_name_to_plural(cls.__model_name__)

            if not getattr(cls, "__display_name__", None):
                cls.__display_name__ = snake_case_to_human(cls.__model_name__)

            if not getattr(cls, "__display_name_plural__", None):
                cls.__display_name_plural__ = model_name_to_plural(cls.__display_name__)

    @classmethod
    def get_display_name(cls):
        return gettext(cls.__display_name__)

    @classmethod
    def get_display_name_plural(cls):
        return gettext(cls.__display_name_plural__)

    @property
    def domain_events(self):
        if not hasattr(self, "_domain_events"):
            self._domain_events: List[events.Event] = []
        return self._domain_events

    def _update_field(
        self,
        command: commands.Command,
        event: events.Event | None,
        field_name: str,
        event_field_name: Optional[str] = None,
    ) -> bool:
        new_value = getattr(command, field_name)
        if new_value == types.unset:
            return False

        old_value = getattr(self, field_name)
        if old_value == new_value:
            return False

        setattr(self, field_name, new_value)

        if event is not None:
            if event_field_name is None:
                event_field_name = field_name

            changed_value = types.ChangedValue(old=old_value, new=new_value)
            setattr(event, event_field_name, changed_value)

        return True

    def __str__(self):  # pragma: no cover
        id = getattr(self, "id", "")
        return f"{self.get_display_name()} {id}"
