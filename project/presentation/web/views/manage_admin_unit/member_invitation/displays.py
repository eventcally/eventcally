from flask_babel import lazy_gettext

from project.presentation.web.modular.base_display import BaseDisplay
from project.presentation.web.modular.base_props import StringProp


class ListDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))


class UpdateDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))
