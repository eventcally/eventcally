from project.api import scope_list
from project.models.oauth import OAuth2Client
from project.permissions import organization_app_permission_infos
from tests.base_test import (
    BaseTestCreateView,
    BaseTestDeleteView,
    BaseTestListView,
    BaseTestReadView,
    BaseTestUpdateView,
)
from tests.views.manage_admin_unit.base_test import ManageAdminUnitChildViewTestMixin


class ObjectViewTestMixin:
    model = OAuth2Client
    endpoint_object_id_arg_name = "app_id"

    def _insert_default_object(self) -> int:
        return self.seeder.insert_default_oauth2_client_app(
            admin_unit_id=self.admin_unit_id,
            created_by_id=self.user_id,
        )


class BaseTestObjectViewMixin(ObjectViewTestMixin, ManageAdminUnitChildViewTestMixin):
    pass


class TestCreateView(BaseTestObjectViewMixin, BaseTestCreateView):
    endpoint_name = "manage_admin_unit.app_create"

    def _fill_form_values(self, values: dict):
        super()._fill_form_values(values)
        values["client_name"] = "Meine App"
        values["scope"] = scope_list
        values["app_permissions"] = [
            i.permission for i in organization_app_permission_infos
        ]
        values["redirect_uris"] = self.utils.get_url("swagger_oauth2_redirect")


class TestReadView(BaseTestObjectViewMixin, BaseTestReadView):
    endpoint_name = "manage_admin_unit.app"


class TestUpdateView(BaseTestObjectViewMixin, BaseTestUpdateView):
    endpoint_name = "manage_admin_unit.app_update"

    def _fill_form_values(self, values: dict, object):
        super()._fill_form_values(values, object)
        values["client_name"] = "Neuer Name"


class TestDeleteView(BaseTestObjectViewMixin, BaseTestDeleteView):
    endpoint_name = "manage_admin_unit.app_delete"

    def _fill_form_values(self, values: dict, object):
        super()._fill_form_values(values, object)
        values["name"] = "Mein Client"


class TestListView(BaseTestObjectViewMixin, BaseTestListView):
    endpoint_name = "manage_admin_unit.apps"
