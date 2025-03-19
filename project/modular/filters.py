from flask_babel import lazy_gettext
from sqlalchemy import func

from project.models.event_category import EventCategory
from project.utils import get_localized_enum_name


class BaseFilter(object):
    def __init__(self, column, **kwargs):
        self.column = column
        self.key = kwargs.get("key", column.key)
        self.label = kwargs.get("label")
        self.options = kwargs.get("options")

    def apply(self, query, value):  # pragma: no cover
        raise NotImplementedError()

    def get_column(self, alias):
        return self.column if alias is None else getattr(alias, self.column.key)

    def __unicode__(self):  # pragma: no cover
        return self.key


class BooleanFilter(BaseFilter):
    def __init__(self, column, **kwargs):
        kwargs.setdefault(
            "options",
            (
                ("", lazy_gettext("All")),
                ("1", lazy_gettext("Yes")),
                ("0", lazy_gettext("No")),
            ),
        )
        super().__init__(
            column,
            **kwargs,
        )

    def apply(self, query, value, alias=None):
        if value == "1":
            return query.filter(self.get_column(alias).is_(True))

        if value == "0":
            return query.filter(self.get_column(alias).is_(False))

        return query  # pragma: no cover


class EnumFilter(BaseFilter):
    def __init__(self, column, **kwargs):
        self.enum_type = column.type._enumtype

        if "options" not in kwargs:
            options = [(-1, lazy_gettext("All"))]

            for e in self.enum_type:
                options.append((int(e), get_localized_enum_name(e)))

            kwargs["options"] = options
        super().__init__(
            column,
            **kwargs,
        )

    def apply(self, query, value, alias=None):
        if value == -1:
            return query

        return query.filter(self.get_column(alias) == value)


class DateRangeFilter(BaseFilter):
    def apply(self, query, value, alias=None):
        from_value = value.get("from_field")
        to_value = value.get("to_field")

        if from_value:
            query = query.filter(self.get_column(alias) >= from_value)

        if to_value:
            query = query.filter(self.get_column(alias) < to_value)

        return query


class SelectModelFilter(BaseFilter):
    def __init__(self, column, loader, **kwargs):
        kwargs.setdefault("key", f"{column.key}_id")
        self.loader = loader
        self.allow_blank = kwargs.get("allow_blank", True)
        super().__init__(
            column,
            **kwargs,
        )

    def apply(self, query, value, alias=None):
        if not value:  # pragma: no cover
            return query

        return query.filter(self.get_column(alias) == value)


class EventCategoryFilter(SelectModelFilter):
    def apply(self, query, value, alias=None):
        if not value:  # pragma: no cover
            return query

        return query.filter(self.get_column(alias).any(EventCategory.id == value.id))


class TagFilter(BaseFilter):
    def apply(self, query, value, alias=None):
        if not value:  # pragma: no cover
            return query

        tags = value if type(value) is list else value.split(",")
        return query.filter(
            (func.string_to_array(self.get_column(alias), ",")).op("@>")(tags)
        )
