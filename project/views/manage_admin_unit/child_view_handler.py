from flask_security import auth_required

from project.access import admin_unit_owner_access_or_401
from project.modular.base_view_handler import BaseViewHandler
from project.views.utils import current_admin_unit


class ManageAdminUnitChildViewHandler(BaseViewHandler):
    decorators = [auth_required()]

    def complete_object(self, object, form):
        super().complete_object(object, form)
        object.admin_unit_id = current_admin_unit.id

    def apply_base_filter(self, query, **kwargs):
        return query.filter(self.model.admin_unit_id == current_admin_unit.id)

    def check_object_access(self, object):
        return admin_unit_owner_access_or_401(object.admin_unit_id)

    def get_id_query_arg_name(self):
        return f"{self.model.__model_name__}_id"
