import pytest


def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)

    url = utils.get_url("api_v1_organization", id=admin_unit_id)
    response = utils.get_ok(url)
    assert "can_verify_other" not in response.json

    seeder.authorize_api_access(user_id, admin_unit_id)

    response = utils.get_json(url)
    assert "can_verify_other" in response.json


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("api_v1_organization_list", keyword="crew")
    utils.get_ok(url)


def test_event_date_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url(
        "api_v1_organization_event_date_search", id=admin_unit_id, sort="-rating"
    )
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 2
    assert response.json["items"][1]["event"]["public_status"] == "draft"


def test_event_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url("api_v1_organization_event_search", id=admin_unit_id)
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_id

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 2
    assert (
        response.json["items"][0]["public_status"] == "draft"
        or response.json["items"][1]["public_status"] == "draft"
    )


def test_organizers(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_organizer_list", id=admin_unit_id, name="crew"
    )
    utils.get_ok(url)


def test_organizers_post(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url("api_v1_organization_organizer_list", id=admin_unit_id)
    response = utils.post_json(url, {"name": "Neuer Organisator"})
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import EventOrganizer

        organizer = (
            EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit_id)
            .filter(EventOrganizer.name == "Neuer Organisator")
            .first()
        )
        assert organizer is not None


def test_events(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_organization_event_list", id=admin_unit_id)
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_id

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 2


def prepare_events_post_data(seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organization_event_list", id=admin_unit_id)
    data = {
        "name": "Fest",
        "start": "2021-02-07T11:00:00.000Z",
        "place": {"id": place_id},
        "organizer": {"id": organizer_id},
        "photo": {"image_base64": seeder.get_default_image_base64()},
    }
    return url, data, admin_unit_id, place_id, organizer_id


@pytest.mark.parametrize("allday", [True, False])
def test_events_post(client, seeder, utils, app, allday):
    url, data, admin_unit_id, place_id, organizer_id = prepare_events_post_data(
        seeder, utils
    )

    if allday:
        data["allday"] = "1"

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import Event, PublicStatus

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Fest")
            .first()
        )
        assert event is not None
        assert event.event_place_id == place_id
        assert event.organizer_id == organizer_id
        assert event.photo is not None
        assert event.photo.encoding_format == "image/png"
        assert event.public_status == PublicStatus.published
        assert event.allday == allday


def test_events_post_co_organizers(client, seeder, utils, app):
    url, data, admin_unit_id, place_id, organizer_id = prepare_events_post_data(
        seeder, utils
    )
    organizer_a_id = seeder.upsert_event_organizer(admin_unit_id, "Organizer A")
    organizer_b_id = seeder.upsert_event_organizer(admin_unit_id, "Organizer B")

    data["co_organizers"] = [
        {"id": organizer_a_id},
        {"id": organizer_b_id},
    ]
    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    event_id = int(response.json["id"])

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        assert len(event.co_organizers) == 2
        assert event.co_organizers[0].id == organizer_a_id
        assert event.co_organizers[1].id == organizer_b_id


def test_events_post_photo_no_data(client, seeder, utils, app):
    url, data, admin_unit_id, place_id, organizer_id = prepare_events_post_data(
        seeder, utils
    )
    data["photo"] = dict()
    response = utils.post_json(url, data)
    utils.assert_response_unprocessable_entity(response)

    error = response.json["errors"][0]
    assert error["field"] == "photo"
    assert error["message"] == "Either image_url or image_base64 has to be defined."


def test_events_post_photo_too_small(client, seeder, utils, app):
    url, data, admin_unit_id, place_id, organizer_id = prepare_events_post_data(
        seeder, utils
    )
    data["photo"][
        "image_base64"
    ] = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="
    response = utils.post_json(url, data)
    utils.assert_response_unprocessable_entity(response)

    error = response.json["errors"][0]
    assert error["field"] == "photo"
    assert error["message"] == "Image is too small (1x1px). At least 320x320px."


def test_places(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id, name="crew")
    utils.get_ok(url)


def test_places_post(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id, name="crew")
    response = utils.post_json(
        url,
        {
            "name": "Neuer Ort",
            "location": {"street": "Straße 1", "postalCode": "38640", "city": "Goslar"},
        },
    )
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
        assert place.name == "Neuer Ort"
        assert place.location.street == "Straße 1"
        assert place.location.postalCode == "38640"
        assert place.location.city == "Goslar"


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


@pytest.mark.parametrize("session_based", [True, False])
def test_outgoing_relation_list(client, seeder, utils, session_based):
    user_id, admin_unit_id = (
        seeder.setup_base() if session_based else seeder.setup_api_access()
    )
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_relation_list",
        id=admin_unit_id,
    )
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == relation_id
    assert response.json["items"][0]["source_organization"]["id"] == admin_unit_id
    assert response.json["items"][0]["target_organization"]["id"] == other_admin_unit_id


def test_outgoing_relation_list_notAuthenticated(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_relation_list",
        id=admin_unit_id,
    )
    response = utils.get_json(url)
    utils.assert_response_unauthorized(response)


def test_outgoing_relation_post(client, app, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url(
        "api_v1_organization_outgoing_relation_list",
        id=admin_unit_id,
    )
    data = {
        "target_organization": {"id": other_admin_unit_id},
        "auto_verify_event_reference_requests": True,
    }

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import AdminUnitRelation

        relation = AdminUnitRelation.query.get(int(response.json["id"]))
        assert relation is not None
        assert relation.source_admin_unit_id == admin_unit_id
        assert relation.target_admin_unit_id == other_admin_unit_id
        assert relation.auto_verify_event_reference_requests


def test_outgoing_relation_post_unknownTarget(client, app, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url(
        "api_v1_organization_outgoing_relation_list",
        id=admin_unit_id,
    )
    data = {
        "target_organization": {"id": 1234},
        "auto_verify_event_reference_requests": True,
    }

    response = utils.post_json(url, data)
    utils.assert_response_unprocessable_entity(response)


def test_outgoing_relation_post_selfReference(client, app, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url(
        "api_v1_organization_outgoing_relation_list",
        id=admin_unit_id,
    )
    data = {
        "target_organization": {"id": admin_unit_id},
        "auto_verify_event_reference_requests": True,
    }

    response = utils.post_json(url, data)
    utils.assert_response_bad_request(response)


def test_organization_invitation_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_organization_invitation_list",
        id=admin_unit_id,
    )
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == invitation_id
    assert response.json["items"][0]["email"] == "invited@test.de"
    assert response.json["items"][0]["organization_name"] == "Invited Organization"


def test_organization_invitation_list_post(client, app, seeder, utils, mocker):
    mail_mock = utils.mock_send_mails(mocker)
    _, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url(
        "api_v1_organization_organization_invitation_list",
        id=admin_unit_id,
    )
    data = {
        "email": "invited@test.de",
        "organization_name": "Invited Organization",
        "relation_auto_verify_event_reference_requests": True,
        "relation_verify": True,
    }

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json
    invitation_id = int(response.json["id"])

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = AdminUnitInvitation.query.get(invitation_id)
        assert invitation is not None
        assert invitation.admin_unit_id == admin_unit_id
        assert invitation.email == "invited@test.de"
        assert invitation.admin_unit_name == "Invited Organization"
        assert invitation.relation_auto_verify_event_reference_requests
        assert invitation.relation_verify

    invitation_url = utils.get_url(
        "user_organization_invitation",
        id=invitation_id,
    )
    utils.assert_send_mail_called(mail_mock, "invited@test.de", invitation_url)
