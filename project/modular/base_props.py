from flask_babel import format_datetime

from project.utils import get_location_str


class BasePropFormatter:
    def format(self, data):  # pragma: no cover
        return data


class ListPropFormatter(BasePropFormatter):
    def format(self, data):
        return ", ".join(data) if isinstance(data, list) else super().format(data)


class DateTimePropFormatter(BasePropFormatter):
    def format(self, data):
        return format_datetime(data)


class LocationPropFormatter(BasePropFormatter):
    def format(self, data):
        return get_location_str(data)


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

    def __init__(self, label=None, name=None, formatter=None, _display=None):
        self.label = label
        self.name = name
        self.formatter = formatter
        self._display = _display

    def get_display_value(self, object):
        if object is not None and hasattr(object, self.name):
            data = getattr(object, self.name)
        else:  # pragma: no cover
            data = None

        return self.formatter.format(data) if self.formatter else data


class StringProp(BaseProp):
    pass


class MethodProp(BaseProp):
    def __init__(self, method_name, *args, **kwargs):
        self.method_name = method_name
        super().__init__(*args, **kwargs)

    def get_display_value(self, object):
        method = getattr(self._display, self.method_name)
        return method(object)


class LocationProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", LocationPropFormatter())
        super().__init__(*args, **kwargs)


class ListProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", ListPropFormatter())
        super().__init__(*args, **kwargs)


class DateTimeProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", DateTimePropFormatter())
        super().__init__(*args, **kwargs)
