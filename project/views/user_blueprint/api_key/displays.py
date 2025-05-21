from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateProp, RateLimitProp, StringProp


class ReadDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    rate_limit_value = RateLimitProp(lazy_gettext("Rate limit"))
    created_at = DateProp(lazy_gettext("Created at"))


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    created_at = DateProp(lazy_gettext("Created at"))
