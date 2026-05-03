from flask import abort, g
from sqlalchemy.orm import class_mapper

from project.utils import getattr_keypath
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class AppChildViewHandler(ManageAdminUnitChildViewHandler):
    app_id_attribute_name = "oauth2_client_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id_column = None
        if self.app_id_attribute_name:
            columns = class_mapper(self.model).columns
            self.app_id_column = columns.get(self.app_id_attribute_name)

    def check_object_access(self, object):
        super().check_object_access(object)

        if not getattr_keypath(object, self.app_id_attribute_name) == g.current_app.id:
            abort(401)

    def complete_object(self, object, form):
        super().complete_object(object, form)
        setattr(object, self.app_id_attribute_name, g.current_app.id)

    def apply_base_filter(self, query, **kwargs):
        query = super().apply_base_filter(query, **kwargs)
        if self.app_id_column is not None:
            query = query.filter(self.app_id_column == g.current_app.id)
        return query

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
                str(g.current_app),
            )
        )

        return result
