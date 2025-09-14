from project.models import AppInstallation
from tests.base_test import (
    BaseTestCreateView,
    BaseTestDeleteView,
    BaseTestListView,
    BaseTestReadView,
    BaseTestUpdateView,
)
from tests.views.manage_admin_unit.base_test import ManageAdminUnitChildViewTestMixin


class ObjectViewTestMixin:
    model = AppInstallation
    endpoint_object_id_arg_name = "app_installation_id"

    def setup_with_fixtures(self):
        super().setup_with_fixtures()

        self.oauth2_client_id = self.seeder.insert_default_oauth2_client_app(
            admin_unit_id=self.admin_unit_id
        )

    def _insert_default_object(self) -> int:
        return self.seeder.install_app(self.oauth2_client_id, self.admin_unit_id)


class BaseTestObjectViewMixin(
    ObjectViewTestMixin,
    ManageAdminUnitChildViewTestMixin,
):
    pass


class TestInstallView(BaseTestObjectViewMixin, BaseTestCreateView):
    endpoint_name = "manage_admin_unit.app_installations_install"

    def _get_endpoint_kwargs(self):
        result = super()._get_endpoint_kwargs()
        result["app_id"] = self.oauth2_client_id
        return result


class TestReadView(BaseTestObjectViewMixin, BaseTestReadView):
    endpoint_name = "manage_admin_unit.app_installation"


class TestAcceptPermissionsView(BaseTestObjectViewMixin, BaseTestUpdateView):
    endpoint_name = "manage_admin_unit.app_installation_accept_permissions"


class TestDeleteView(BaseTestObjectViewMixin, BaseTestDeleteView):
    endpoint_name = "manage_admin_unit.app_installation_delete"


class TestListView(BaseTestObjectViewMixin, BaseTestListView):
    endpoint_name = "manage_admin_unit.app_installations"
