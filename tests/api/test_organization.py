def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("api_v1_organization", id=admin_unit_id)
    utils.get_ok(url)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("api_v1_organization_list", keyword="crew")
    utils.get_ok(url)


def test_event_date_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_organization_event_date_search", id=admin_unit_id)
    utils.get_ok(url)


def test_event_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_organization_event_search", id=admin_unit_id)
    utils.get_ok(url)


def test_organizers(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_organizer_list", id=admin_unit_id, name="crew"
    )
    utils.get_ok(url)


def test_places(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id, name="crew")
    utils.get_ok(url)


def test_places_post(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id, name="crew")
    response = utils.post_json(url, {"name": "Neuer Ort"})
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import EventPlace

        place = (
            EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)
            .filter(EventPlace.name == "Neuer Ort")
            .first()
        )
        assert place is not None


def test_references_incoming(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_list",
        id=admin_unit_id,
        name="crew",
    )
    utils.get_ok(url)


def test_references_outgoing(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_list",
        id=admin_unit_id,
        name="crew",
    )
    utils.get_ok(url)
