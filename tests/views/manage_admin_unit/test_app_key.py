from project.models import AppKey
from tests.base_test import (
    BaseTestCreateView,
    BaseTestDeleteView,
    BaseTestListView,
    BaseTestReadView,
)
from tests.views.manage_admin_unit.base_test import ManageAdminUnitChildViewTestMixin


class ManageAdminUnitAppChildViewTestMixin:
    oauth2_client_id: int = None

    def setup_with_fixtures(self):
        super().setup_with_fixtures()

        self.oauth2_client_id = self.seeder.insert_default_oauth2_client_app(
            admin_unit_id=self.admin_unit_id
        )

    def _get_endpoint_kwargs(self) -> dict:
        result = super()._get_endpoint_kwargs()
        result["app_id"] = self.oauth2_client_id
        return result


class ObjectViewTestMixin:
    model = AppKey
    endpoint_object_id_arg_name = "app_key_id"

    def _insert_default_object(self) -> int:
        _, app_key_id = self.seeder.insert_app_key(self.oauth2_client_id)
        return app_key_id


class BaseTestObjectViewMixin(
    ObjectViewTestMixin,
    ManageAdminUnitAppChildViewTestMixin,
    ManageAdminUnitChildViewTestMixin,
):
    pass


class TestCreateView(BaseTestObjectViewMixin, BaseTestCreateView):
    endpoint_name = "manage_admin_unit.app.app_key_create"

    def test(self):
        super().test()

        # Test download PEM
        endpoint_kwargs = self._get_endpoint_kwargs()
        endpoint_kwargs["app_key_id"] = self.object_id
        endpoint_kwargs["download_pem"] = 1
        url = self.utils.get_url("manage_admin_unit.app.app_key", **endpoint_kwargs)
        self.utils.get_ok(url)


class TestReadView(BaseTestObjectViewMixin, BaseTestReadView):
    endpoint_name = "manage_admin_unit.app.app_key"


class TestDeleteView(BaseTestObjectViewMixin, BaseTestDeleteView):
    endpoint_name = "manage_admin_unit.app.app_key_delete"

    def _fill_form_values(self, values: dict, object):
        super()._fill_form_values(values, object)
        values["kid"] = object.kid


class TestListView(BaseTestObjectViewMixin, BaseTestListView):
    endpoint_name = "manage_admin_unit.app.app_keys"
