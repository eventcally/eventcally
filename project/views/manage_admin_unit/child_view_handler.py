from flask_security import auth_required
from sqlalchemy.orm import class_mapper

from project.access import admin_unit_owner_access_or_401
from project.modular.base_view_handler import BaseViewHandler
from project.views.utils import current_admin_unit


class ManageAdminUnitChildViewHandler(BaseViewHandler):
    decorators = [auth_required()]
    admin_unit_id_attribute_name = "admin_unit_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_unit_id_column = class_mapper(self.model).columns[
            self.admin_unit_id_attribute_name
        ]

    def complete_object(self, object, form):
        super().complete_object(object, form)
        setattr(object, self.admin_unit_id_attribute_name, current_admin_unit.id)

    def apply_base_filter(self, query, **kwargs):
        return (
            super()
            .apply_base_filter(query, **kwargs)
            .filter(self.admin_unit_id_column == current_admin_unit.id)
        )

    def check_object_access(self, object):
        return admin_unit_owner_access_or_401(
            getattr(object, self.admin_unit_id_attribute_name)
        )

    def get_id_query_arg_name(self):
        return f"{self.model.__model_name__}_id"
