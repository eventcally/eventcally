def test_authorization_code(seeder):
    user_id, admin_unit_id = seeder.setup_api_access()


def test_refresh_token(seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    utils.refresh_token()
