import pytest


def test_read(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("event_reference", id=reference_id)
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils, seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("event_reference_create", event_id=event_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": admin_unit_id},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "event", event_id=event_id)

    with app.app_context():
        from project.models import EventReference

        reference = (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id)
            .first()
        )
        assert reference is not None


def test_create_401(client, app, utils, seeder, mocker):
    seeder.create_user()
    seeder._utils.login()

    owner_id = seeder.create_user("owner@owner")
    other_admin_unit_id = seeder.create_admin_unit(owner_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("event_reference_create", event_id=event_id)
    response = client.get(url)
    assert response.status_code == 401


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder, utils, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("event_reference_update", id=reference_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "rating": 70,
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_references_incoming", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventReference

        reference = EventReference.query.get(reference_id)
        assert reference.rating == 70


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_delete(client, seeder, utils, app, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("reference_delete", id=reference_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Name"

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
        utils.assert_response_error_message(
            response,
            b"Der eingegebene Name entspricht nicht dem Namen der Veranstaltung",
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_references_incoming", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventReference

        reference = EventReference.query.get(reference_id)
        assert reference is None


def test_admin_unit_references_incoming(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    utils.get_endpoint_ok("manage_admin_unit_references_incoming", id=admin_unit_id)


def test_admin_unit_references_outgoing(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    utils.get_endpoint_ok("manage_admin_unit_references_outgoing", id=admin_unit_id)


def test_referencedEventUpdate_sendsMail(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    utils.logout()
    utils.login("other@test.de")
    url = utils.get_url("event_update", event_id=event_id)
    response = utils.get_ok(url)

    mail_mock = utils.mock_send_mails(mocker)
    response = utils.post_form(
        url,
        response,
        {
            "name": "Changed name",
        },
    )

    utils.assert_send_mail_called(mail_mock, "test@test.de")
