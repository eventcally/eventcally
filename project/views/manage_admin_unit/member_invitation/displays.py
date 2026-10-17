from flask_babel import lazy_gettext

from project.views.modular.base_display import BaseDisplay
from project.views.modular.base_props import StringProp


class ListDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))


class UpdateDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))
