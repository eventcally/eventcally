class ManageAdminUnitChildViewTestMixin:
    user_id: int = None
    admin_unit_id: int = None

    def setup_with_fixtures(self):
        super().setup_with_fixtures()

        self.user_id, self.admin_unit_id = self.seeder.setup_base(True)

    def _get_endpoint_kwargs(self) -> dict:
        result = super()._get_endpoint_kwargs()
        result["id"] = self.admin_unit_id
        return result
