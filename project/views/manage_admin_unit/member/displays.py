from flask_babel import gettext, lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BasePropFormatter, StringProp


class RolesPropFormatter(BasePropFormatter):
    def format(self, data):
        title_list = [gettext(role.title) for role in data]
        return ", ".join(title_list)


class ListDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"), keypath="user.email")
    roles = StringProp(lazy_gettext("Roles"), formatter=RolesPropFormatter())


class UpdateDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"), keypath="user.email")
