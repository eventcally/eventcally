from flask_babel import format_date, format_datetime

from project.presentation.shared.permissions import get_organization_permission_infos
from project.shared.utils import getattr_keypath


class BasePropFormatter:
    def format(self, data):  # pragma: no cover
        return data


class ListPropFormatter(BasePropFormatter):
    def format(self, data):
        return ", ".join(data) if isinstance(data, list) else super().format(data)


class DateTimePropFormatter(BasePropFormatter):
    def format(self, data):
        return format_datetime(data) if data else ""


class DatePropFormatter(BasePropFormatter):
    def format(self, data):
        return format_date(data) if data else ""


class StringPropFormatter(BasePropFormatter):
    def format(self, data):
        return data if data is not None else ""


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
        no_wrap=False,
        icon=None,
        _display=None,
    ):
        self.label = label
        self.name = name
        self.formatter = formatter
        self.keypath = keypath
        self.method_name = method_name
        self.link_method_name = link_method_name
        self.no_wrap = no_wrap
        self.icon = icon
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


class CountProp(BaseProp):  # pragma: no cover
    def get_display_data(self, object):
        data = super().get_display_data(object)
        return len(data) if hasattr(data, "__len__") else None


class OrganizationAppPermissionListPropFormatter(BasePropFormatter):
    def format(self, data):
        labels = [str(i.label) for i in get_organization_permission_infos(data)]
        return ", ".join(labels)


class OrganizationAppPermissionListProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", OrganizationAppPermissionListPropFormatter())
        super().__init__(*args, **kwargs)


class URLPropFormatter(StringPropFormatter):
    pass


class URLProp(BaseProp):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter", URLPropFormatter())
        super().__init__(*args, **kwargs)

    def get_link(self, object):
        return self.get_display_data(object)
