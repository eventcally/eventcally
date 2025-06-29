from tests.seeder import Seeder
from tests.utils import UtilActions


def test_authorization_code(seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_api_access()


def test_legacy(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    authorize_scope = "profile event:write organizer:write place:write"
    seeder.authorize_api_access(user_id, admin_unit_id, authorize_scope=authorize_scope)
    utils.refresh_token()


def test_refresh_token(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    utils.refresh_token()
