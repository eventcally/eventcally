from flask_babel import lazy_gettext
from flask_security import roles_required

from project.modular.base_views import BaseView


class AdminView(BaseView):
    decorators = [roles_required("admin")]
    template_file_name = "admin.html"

    def get_title(self, **kwargs):
        return lazy_gettext("Admin")
