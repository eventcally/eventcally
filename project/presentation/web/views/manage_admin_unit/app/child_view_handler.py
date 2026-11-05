from flask import abort, g

from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.shared.utils import getattr_keypath


class AppChildViewHandler(ManageAdminUnitChildViewHandler):
    app_id_attribute_name = "oauth2_client_id"

    def check_object_access(self, object):
        super().check_object_access(object)

        if not getattr_keypath(object, self.app_id_attribute_name) == g.current_app.id:
            abort(401)
