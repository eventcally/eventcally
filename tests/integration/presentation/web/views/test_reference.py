import pytest


def test_read(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    # A shell: the Vue page reads through the BFF.
    response = utils.get_ok(url)
    assert b'id="app"' in response.data


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils, seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
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

    utils.assert_response_redirect(response, "main.event", event_id=event_id)

    with app.app_context():
        from project.infrastructure.models import EventReference

        reference = (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id)
            .first()
        )
        assert reference is not None


def test_create_duplicateNotAllowed(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": admin_unit_id},
    )
    utils.assert_response_ok(response)
    assert b"duplicate key" in response.data


def test_create_401(client, app, utils, seeder, mocker):
    seeder.create_user()
    seeder._utils.login()

    owner_id = seeder.create_user("owner@owner")
    other_admin_unit_id = seeder.create_admin_unit(owner_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
    response = client.get(url)
    assert response.status_code == 401


def test_create_401_without_other_organization_to_reference_from(
    client, app, utils, seeder
):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("main.event_reference_create", event_id=event_id)
    response = client.get(url)
    assert response.status_code == 401


def test_read_of_another_organization_is_401(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _, _, _, reference_id = seeder.create_any_reference(admin_unit_id)
    second_admin_unit_id = seeder.create_admin_unit(user_id, "Zweite Crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.incoming_event_reference",
            id=second_admin_unit_id,
            event_reference_id=reference_id,
        )
    )


def test_read_unknown_is_404(seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get(
        utils.get_url(
            "manage_admin_unit.incoming_event_reference",
            id=admin_unit_id,
            event_reference_id=4711,
        )
    )

    utils.assert_response_notFound(response)


@pytest.mark.parametrize("action", ["update", "delete"])
def test_update_and_delete_pages_are_gone(seeder, utils, action):
    # The rating edit and the delete are modals of the Vue pages.
    _, admin_unit_id = seeder.setup_base()
    _, _, _, reference_id = seeder.create_any_reference(admin_unit_id)

    response = utils.get(
        f"/manage/admin_unit/{admin_unit_id}/incoming_event_reference/{reference_id}/{action}"
    )

    utils.assert_response_notFound(response)


def test_admin_unit_references_incoming(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.incoming_event_references", id=admin_unit_id
    )


def test_admin_unit_references_outgoing(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.outgoing_event_references", id=admin_unit_id
    )
