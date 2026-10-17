from flask_babel import lazy_gettext

from project.presentation.web.modular.base_display import BaseDisplay
from project.presentation.web.modular.base_props import StringProp


class ReadDisplay(BaseDisplay):
    kid = StringProp(lazy_gettext("KID"))
    checksum = StringProp(lazy_gettext("Checksum"))


class ListDisplay(BaseDisplay):
    kid = StringProp(lazy_gettext("KID"))
