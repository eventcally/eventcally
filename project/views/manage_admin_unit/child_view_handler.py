from typing import Annotated

from dependency_injector.wiring import Provide
from flask_security import auth_required
from sqlalchemy.orm import class_mapper

from project.access import admin_unit_owner_access_or_401
from project.modular.base_view_handler import BaseViewHandler
from project.services.organization_service import OrganizationService
from project.views.utils import current_admin_unit, manage_permission_required


class ManageAdminUnitBaseViewHandler(BaseViewHandler):
    decorators = [auth_required()]
    organization_service: Annotated[
        OrganizationService, Provide["services.organization_service"]
    ]

    def _add_view(self, key, url, view_class, endpoint, app, **kwargs):
        if (
            view_class.permission is None and view_class.permission_action is None
        ):  # pragma: no cover
            raise ValueError("permission or permission_action must be set")

        if view_class.permission is None:
            view_class.permission = (
                f"{self.get_permission_entity()}:{view_class.permission_action.name}"
            )

        decorator = manage_permission_required(view_class.permission)
        decorators = kwargs.setdefault("decorators", [])
        decorators.append(decorator)
        self.permissions.add(view_class.permission)

        return super()._add_view(key, url, view_class, endpoint, app, **kwargs)


class ManageAdminUnitChildViewHandler(ManageAdminUnitBaseViewHandler):
    admin_unit_id_attribute_name = "admin_unit_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.admin_unit_id_attribute_name:
            self.admin_unit_id_column = class_mapper(self.model).columns[
                self.admin_unit_id_attribute_name
            ]

    def complete_object(self, object, form):
        super().complete_object(object, form)

        if self.admin_unit_id_attribute_name:
            setattr(object, self.admin_unit_id_attribute_name, current_admin_unit.id)

    def apply_base_filter(self, query, **kwargs):
        assert hasattr(
            self, "admin_unit_id_column"
        ), "admin_unit_id_column is not set. Override apply_base_filter if admin_unit_id_column is not used."

        return (
            super()
            .apply_base_filter(query, **kwargs)
            .filter(self.admin_unit_id_column == current_admin_unit.id)
        )

    def check_object_access(self, object):
        assert (
            self.admin_unit_id_attribute_name
        ), "admin_unit_id_attribute_name is not set. Override check_object_access if this attribute is not used."

        return admin_unit_owner_access_or_401(
            getattr(object, self.admin_unit_id_attribute_name)
        )

    def get_id_query_arg_name(self):
        return f"{self.get_model_name()}_id"
