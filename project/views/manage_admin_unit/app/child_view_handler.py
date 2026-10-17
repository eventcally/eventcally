from flask import abort, g

from project.utils import getattr_keypath
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class AppChildViewHandler(ManageAdminUnitChildViewHandler):
    app_id_attribute_name = "oauth2_client_id"

    def check_object_access(self, object):
        super().check_object_access(object)

        if not getattr_keypath(object, self.app_id_attribute_name) == g.current_app.id:
            abort(401)

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()

        result.append(
            self._create_breadcrumb(
                self.parent.get_list_url(),
                self.parent.get_model_display_name_plural(),
            )
        )
        result.append(
            self._create_breadcrumb(
                self.parent.get_read_url(g.current_app),
                self.parent.get_object_title(g.current_app),
            )
        )

        return result
