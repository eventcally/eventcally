from flask import url_for
from flask_babel import gettext
from flask_security import auth_required

from project.access import owner_access_or_401
from project.modular.base_view_handler import BaseViewHandler


class UserChildViewHandler(BaseViewHandler):
    decorators = [auth_required()]

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()
        result.append(
            self._create_breadcrumb(url_for("main.profile"), gettext("Profile"))
        )
        return result

    def check_object_access(self, object):
        return owner_access_or_401(object.user_id)

    def get_id_query_arg_name(self):
        return f"{self.get_model_name()}_id"
