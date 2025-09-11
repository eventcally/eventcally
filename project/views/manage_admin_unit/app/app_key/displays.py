from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import StringProp


class ReadDisplay(BaseDisplay):
    kid = StringProp(lazy_gettext("KID"))
    checksum = StringProp(lazy_gettext("Checksum"))


class ListDisplay(BaseDisplay):
    kid = StringProp(lazy_gettext("KID"))
