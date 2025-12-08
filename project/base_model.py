from flask_babel import gettext
from flask_sqlalchemy.model import Model as SQLAlchemyModel

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

    def __str__(self):  # pragma: no cover
        id = getattr(self, "id", "")
        return f"{self.get_display_name()} {id}"
