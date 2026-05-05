from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateTimeProp, StringProp


class ReadDisplay(BaseDisplay):
    id = StringProp(lazy_gettext("ID"))
    start_at = DateTimeProp(lazy_gettext("Start at"))
    end_at = DateTimeProp(lazy_gettext("End at"))
    url = StringProp(lazy_gettext("URL"))
    status = StringProp(lazy_gettext("Status"))
    status_code = StringProp(lazy_gettext("Status code"))


class ListDisplay(BaseDisplay):
    id = StringProp(lazy_gettext("ID"))
    start_at = DateTimeProp(lazy_gettext("Start at"))
    end_at = DateTimeProp(lazy_gettext("End at"))
    url = StringProp(lazy_gettext("URL"))
    status = StringProp(lazy_gettext("Status"))
    status_code = StringProp(lazy_gettext("Status code"))
