from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_authorization_code(seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_api_access()


def test_legacy(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    authorize_scope = "profile event:write organizer:write place:write"
    seeder.authorize_api_access(user_id, admin_unit_id, authorize_scope=authorize_scope)
    utils.refresh_token()


def test_legacy_client_credentials(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = seeder.insert_default_oauth2_client(user_id)

    with seeder._app.app_context():
        from project.infrastructure.models import OAuth2Client

        client = seeder._db.session.get(OAuth2Client, oauth2_client_id)
        client_id = client.client_id
        client_secret = client.client_secret

    utils.grant_client_credentials(
        client_id, client_secret, "event:write organizer:write"
    )


def test_refresh_token(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    utils.refresh_token()


def test_jwt_bearer_grant(app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import OAuth2Client
        from project.infrastructure.seed_helpers import add_keypair_to_oauth2_client

        oauth2_client = OAuth2Client.query.get(oauth2_client_id)

        add_keypair_to_oauth2_client(oauth2_client)
        private_pem, app_key = add_keypair_to_oauth2_client(oauth2_client)
        kid = app_key.kid
        db.session.commit()

    # Authorize as app
    utils.authorize_as_app(oauth2_client_id, private_pem, kid)

    # Get installations
    app_installation_id = seeder.install_app(oauth2_client_id, admin_unit_id)
    url = utils.get_url(
        "api_v1_app_installation_list",
    )
    response = utils.get_json(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == app_installation_id

    # Get installation
    url = utils.get_url("api_v1_app_installation", id=app_installation_id)
    response = utils.get_json(url)
    assert response.json["id"] == app_installation_id

    # Authorize as app installation
    utils.authorize_as_app_installation(app_installation_id, private_pem, kid)

    # Get protected resource with app installation token
    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_list", id=admin_unit_id
    )
    response = utils.get_json_ok(url)

    # Can't get installation list with installation token
    url = utils.get_url(
        "api_v1_app_installation_list",
    )
    response = utils.get_json(url)
    utils.assert_response_bad_request(response)


def test_revoke_token_revokes_the_access_token(app, db, seeder: Seeder, utils):
    seeder.setup_api_access()
    access_token = utils.get_access_token()

    utils.revoke_token()

    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        token = OAuth2Token.query.filter_by(access_token=access_token).first()
        assert token.is_revoked()


def test_introspect_finds_tokens_with_and_without_hint(seeder: Seeder, utils):
    seeder.setup_api_access()

    utils.introspect(utils.get_access_token(), "access_token")
    utils.introspect(utils.get_refresh_token(), "refresh_token")
    utils.introspect(utils.get_access_token(), "")
    utils.introspect(utils.get_refresh_token(), "")


def test_jwt_bearer_grant_rejects_wrong_audience(app, db, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import OAuth2Client
        from project.infrastructure.seed_helpers import add_keypair_to_oauth2_client

        oauth2_client = OAuth2Client.query.get(oauth2_client_id)
        private_pem, app_key = add_keypair_to_oauth2_client(oauth2_client)
        kid = app_key.kid
        db.session.commit()

    response = utils.post_jwt_bearer_assertion(
        oauth2_client_id, private_pem, kid, "https://evil.example/token"
    )

    utils.assert_response_bad_request(response)
    assert response.json["error"] == "invalid_grant"
