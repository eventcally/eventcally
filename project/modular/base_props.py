from flask_babel import format_date, format_datetime
from markupsafe import Markup

from project.utils import get_localized_enum_name, get_location_str, getattr_keypath


class BasePropFormatter:
    def format(self, data):  # pragma: no cover
        return data


class ListPropFormatter(BasePropFormatter):
    def format(self, data):
        return ", ".join(data) if isinstance(data, list) else super().format(data)


class DateTimePropFormatter(BasePropFormatter):
    def format(self, data):
        return format_datetime(data)


class DatePropFormatter(BasePropFormatter):
    def format(self, data):
        return format_date(data) if data else ""


class StringPropFormatter(BasePropFormatter):
    def format(self, data):
        return data or ""


class LocationPropFormatter(BasePropFormatter):
    def format(self, data):
        return get_location_str(data)


class EventPropFormatter(BasePropFormatter):
    def format(self, data):
        return data.name


class EnumPropFormatter(BasePropFormatter):
    def format(self, data):
        return get_localized_enum_name(data) if data else ""


class BadgePropFormatter(EnumPropFormatter):
    badge_mapping = dict()

    def format(self, data):
        localized = super().format(data)
        if not localized:  # pragma: no cover
            return localized

        badge_class = self.badge_mapping[data]
        return Markup(
            f'<span class="badge badge-pill badge-{badge_class}">{localized}</span>'
        )


class UnboundProp:
    _is_prop = True
    creation_counter = 0

    def __init__(self, field_class, *args, name=None, **kwargs):
        UnboundProp.creation_counter += 1
        self.field_class = field_class
        self.args = args
        self.name = name
        self.kwargs = kwargs
        self.creation_counter = UnboundProp.creation_counter

    def bind(self, display, name, **kwargs):
        kw = dict(
            self.kwargs,
            name=name,
            _display=display,
            **kwargs,
        )
        return self.field_class(*self.args, **kw)


class BaseProp:
    def __new__(cls, *args, **kwargs):
        if "_display" in kwargs:
            return super().__new__(cls)
        else:
            return UnboundProp(cls, *args, **kwargs)

    def __init__(
        self,
        label=None,
        name=None,
        formatter=None,
        keypath=None,
        method_name=None,
        link_method_name=None,
        hide_when_empty=False,
        _display=None,
    ):
        self.label = label
        self.name = name
        self.formatter = formatter
        self.keypath = keypath
        self.method_name = method_name
        self.link_method_name = link_method_name
        self.hide_when_empty = hide_when_empty
        self._display = _display

    def get_display_data(self, object):
        if self.method_name:
            method = getattr(self._display, self.method_name)
            return method(object)

        if object is not None:
            if self.keypath:
                return getattr_keypath(object, self.keypath)

            if hasattr(object, self.name):
                return getattr(object, self.name)

        return None  # pragma: no cover

    def get_display_value(self, object):
        data = self.get_display_data(object)
        return self.formatter.format(data) if self.formatter else data

    def should_display(self, object):
        if not self.hide_when_empty:
            return True

        return self.get_display_value(object)

    def get_link(self, object):
        if not self.link_method_name:
            return None

        method = getattr(self._display, self.link_method_name)
        return method(object)


class StringProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", StringPropFormatter())
        super().__init__(*args, **kwargs)


class IntProp(StringProp):
    pass


class LocationProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", LocationPropFormatter())
        super().__init__(*args, **kwargs)


class EventProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", EventPropFormatter())
        super().__init__(*args, **kwargs)


class EnumProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", EnumPropFormatter())
        super().__init__(*args, **kwargs)


class ListProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", ListPropFormatter())
        super().__init__(*args, **kwargs)


class DateTimeProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", DateTimePropFormatter())
        super().__init__(*args, **kwargs)


class DateProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", DatePropFormatter())
        super().__init__(*args, **kwargs)


class BoolProp(BaseProp):
    def get_display_data(self, object):
        data = super().get_display_data(object)
        return True if data else False


class CountProp(BaseProp):  # pragma: no cover
    def get_display_data(self, object):
        data = super().get_display_data(object)
        return len(data) if hasattr(data, "__len__") else None
