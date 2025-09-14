from flask import g
from sqlalchemy.orm import class_mapper

from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class AppChildViewHandler(ManageAdminUnitChildViewHandler):
    app_id_attribute_name = "oauth2_client_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id_column = class_mapper(self.model).columns[
            self.app_id_attribute_name
        ]

    def complete_object(self, object, form):
        super().complete_object(object, form)
        setattr(object, self.app_id_attribute_name, g.current_app.id)

    def apply_base_filter(self, query, **kwargs):
        return (
            super()
            .apply_base_filter(query, **kwargs)
            .filter(self.app_id_column == g.current_app.id)
        )

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
