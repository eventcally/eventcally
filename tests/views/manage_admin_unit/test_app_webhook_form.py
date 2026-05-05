"""Tests for webhook form create/update command methods in app views."""

from project.api import scope_list
from project.permissions import organization_app_permission_infos
from tests.seeder import Seeder
from tests.utils import UtilActions


def test_app_create_with_webhook_url(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin=True)

    url = utils.get_url("manage_admin_unit.app_create", id=admin_unit_id)
    response = utils.get_ok(url)

    values = {
        "client_name": "Test App With Webhook",
        "scope": scope_list,
        "app_permissions": [i.permission for i in organization_app_permission_infos],
        "redirect_uris": utils.get_url("main.swagger_oauth2_redirect"),
        "webhook-url": "https://example.test/webhook",
        "webhook-secret": "mysecret",
    }
    utils.post_form(url, response, values)


def test_app_update_with_webhook_url(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id, created_by_id=user_id
    )

    url = utils.get_url("manage_admin_unit.app_update", id=admin_unit_id, app_id=app_id)
    response = utils.get_ok(url)

    values = {
        "client_name": "Updated App With Webhook",
        "scope": scope_list,
        "app_permissions": [i.permission for i in organization_app_permission_infos],
        "redirect_uris": utils.get_url("main.swagger_oauth2_redirect"),
        "webhook-url": "https://example.test/webhook",
        "webhook-secret": "mysecret",
    }
    utils.post_form(url, response, values)
