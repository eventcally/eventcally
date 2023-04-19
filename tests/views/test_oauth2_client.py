import pytest


def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(True)
    oauth2_client_id = seeder.insert_default_oauth2_client(user_id)

    url = utils.get_url("oauth2_client", id=oauth2_client_id)
    utils.get_ok(url)


def test_read_notOwner(client, seeder, utils):
    user_id = seeder.create_user(email="other@other.de", admin=True)
    oauth2_client_id = seeder.insert_default_oauth2_client(user_id)

    seeder.setup_base(True)
    url = utils.get_url("oauth2_client", id=oauth2_client_id)
    utils.get_unauthorized(url)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("oauth2_clients")
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
def test_create_authorization_code(client, app, utils, seeder, mocker, db_error):
    from project.api import scope_list

    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("oauth2_client_create")
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "client_name": "Mein Client",
            "scope": scope_list,
            "redirect_uris": utils.get_url("swagger_oauth2_redirect"),
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    with app.app_context():
        from project.models import OAuth2Client

        oauth2_client = OAuth2Client.query.filter(
            OAuth2Client.user_id == user_id
        ).first()
        assert oauth2_client is not None
        client_id = oauth2_client.id

    utils.assert_response_redirect(response, "oauth2_client", id=client_id)


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder, utils, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base(True)
    oauth2_client_id = seeder.insert_default_oauth2_client(user_id)

    url = utils.get_url("oauth2_client_update", id=oauth2_client_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "client_name": "Neuer Name",
            "redirect_uris": "localhost:1337\nlocalhost:1338",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "oauth2_client", id=oauth2_client_id)

    with app.app_context():
        from project.models import OAuth2Client

        oauth2_client = db.session.get(OAuth2Client, oauth2_client_id)
        assert oauth2_client.client_name == "Neuer Name"
        assert oauth2_client.redirect_uris == ["localhost:1337", "localhost:1338"]


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base(True)
    oauth2_client_id = seeder.insert_default_oauth2_client(user_id)

    url = utils.get_url("oauth2_client_delete", id=oauth2_client_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Mein Client"

    if non_match:
        form_name = "Falscher Name"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if non_match:
        utils.assert_response_error_message(response)
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "oauth2_clients")

    with app.app_context():
        from project.models import OAuth2Client

        oauth2_client = db.session.get(OAuth2Client, oauth2_client_id)
        assert oauth2_client is None
