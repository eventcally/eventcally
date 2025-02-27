from flask import url_for
from flask_babel import gettext
from flask_security import roles_required

from project.modular.base_view_handler import BaseViewHandler


class AdminChildViewHandler(BaseViewHandler):
    decorators = [roles_required("admin")]

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()
        result.append(self._create_breadcrumb(url_for("admin.admin"), gettext("Admin")))
        return result
