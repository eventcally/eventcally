"""Filter options of the query-backed lists.

A filter only builds a field of the list form; the view handler maps the field's value
onto its list query (`create_list_query`), so the read repository does the filtering.
"""

from flask_babel import lazy_gettext

from project.shared.utils import get_localized_enum_name


class BaseFilter(object):
    def __init__(self, key, **kwargs):
        self.key = key
        self.label = kwargs.get("label")
        self.options = kwargs.get("options")

    def __unicode__(self):  # pragma: no cover
        return self.key


class BooleanFilter(BaseFilter):
    """Form value "" (all), "1" or "0"."""

    def __init__(self, key, **kwargs):
        kwargs.setdefault(
            "options",
            (
                ("", lazy_gettext("All")),
                ("1", lazy_gettext("Yes")),
                ("0", lazy_gettext("No")),
            ),
        )
        super().__init__(key, **kwargs)


class EnumFilter(BaseFilter):
    """`enum_name` keeps the msgids of a differently named enum; the form value is the
    member's int or -1 for all."""

    def __init__(self, key, enum_type, **kwargs):
        self.enum_type = enum_type
        enum_name = kwargs.pop("enum_name", None)

        if "options" not in kwargs:
            options = [(-1, lazy_gettext("All"))]

            for e in self.enum_type:
                options.append((int(e), get_localized_enum_name(e, enum_name)))

            kwargs["options"] = options

        super().__init__(key, **kwargs)


# The names the view handlers use.
KeyBooleanFilter = BooleanFilter
KeyEnumFilter = EnumFilter


def enum_filter_value_or_none(enum_type, value):
    """Map an `EnumFilter` form value onto `enum_type`; "all" (-1), empty and
    unknown values mean no filter."""
    try:
        return enum_type(int(value))
    except (TypeError, ValueError):
        return None
