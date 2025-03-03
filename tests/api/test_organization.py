import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)

    url = utils.get_url("api_v1_organization", id=admin_unit_id)
    response = utils.get_json_ok(url)
    assert "can_verify_other" not in response.json

    seeder.authorize_api_access(user_id, admin_unit_id)

    response = utils.get_json_ok(url)
    assert "can_verify_other" in response.json


def test_list(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_api_access(user_access=False)
    url = utils.get_url("api_v1_organization_list", keyword="crew")
    utils.get_json_ok(url)


def test_list_postal_code(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_api_access(user_access=False)
    url = utils.get_url("api_v1_organization_list", postal_code="38640,38690")
    utils.get_json_ok(url)


def test_list_for_reference_request(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("api_v1_organization_list", for_reference_request="1")
    response = utils.get_json_ok(url, headers={"X-OrganizationId": str(admin_unit_id)})

    assert len(response.json["items"]) == 2
    assert response.json["items"][1]["id"] == other_admin_unit_id


def test_list_unverified(client, app, seeder: Seeder, utils: UtilActions):
    user_id, verified_admin_unit_id = seeder.setup_base(
        email="verified@test.de",
        log_in=False,
        name="Verified",
        admin_unit_verified=True,
    )
    _, unverified_admin_unit_id = seeder.setup_base(
        email="unverified@test.de",
        log_in=False,
        name="Unverified",
        admin_unit_verified=False,
    )
    seeder.grant_client_credentials_api_access(user_id)

    # Unauthorisierte Nutzer sehen nur verifizierte Organisationen
    url = utils.get_url("api_v1_organization_list")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == verified_admin_unit_id

    # user_id1 sieht verified_admin_unit_id, weil sie verifiziert ist,
    # aber nicht unverified_admin_unit_id, weil sie nicht verifiziert ist.
    utils.login("verified@test.de")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == verified_admin_unit_id

    # Authorisierte Nutzer, die Organisationen verifizieren dürfen, sehen alle Organisationen.
    # "admin@eventcally.com" ist Mitglied der Organisation "eventcally", die andere Organisationen verifizieren darf.
    with app.app_context():
        from project.services.admin_unit import get_admin_unit_by_name

        eventcally_id = get_admin_unit_by_name("eventcally").id

    utils.logout()
    utils.login("admin@eventcally.com")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 3
    assert response.json["items"][0]["id"] == eventcally_id
    assert response.json["items"][1]["id"] == unverified_admin_unit_id
    assert response.json["items"][2]["id"] == verified_admin_unit_id

    # Globale Admins dürfen alle Organisationen sehen
    seeder.create_user("admin@test.de", admin=True)
    utils.logout()
    utils.login("admin@test.de")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 3


def test_event_date_search(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url(
        "api_v1_organization_event_date_search", id=admin_unit_id, sort="-rating"
    )
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 2
    assert response.json["items"][1]["event"]["public_status"] == "draft"


def test_event_search(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url("api_v1_organization_event_search", id=admin_unit_id)
    response = utils.get_json_ok(url)
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

    seeder.create_any_reference(admin_unit_id)
    url = utils.get_url(
        "api_v1_organization_event_search",
        id=admin_unit_id,
        include_organization_references="yes",
    )
    response = utils.get_json_ok(url)

    url = utils.get_url(
        "api_v1_organization_event_search",
        id=admin_unit_id,
        organization_references_only="yes",
    )
    response = utils.get_json_ok(url)


def test_organizers(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organization_organizer_list", id=admin_unit_id)
    utils.get_json_ok(url)

    url = utils.get_url(
        "api_v1_organization_organizer_list", id=admin_unit_id, name="crew"
    )
    utils.get_json_ok(url)


def test_organizers_post(client, seeder: Seeder, utils: UtilActions, app):
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


def test_events(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_organization_event_list", id=admin_unit_id)
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_id

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 2


def prepare_events_post_data(seeder, utils, legacy=False):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organization_event_list", id=admin_unit_id)
    data = {
        "name": "Fest",
        "place": {"id": place_id},
        "organizer": {"id": organizer_id},
        "photo": {
            "image_base64": seeder.get_default_image_base64(),
            "copyright_text": "EventCally",
        },
    }

    if legacy:
        data["start"] = "2021-02-07T11:00:00.000Z"
    else:
        data["date_definitions"] = [{"start": "2021-02-07T11:00:00.000Z"}]

    return url, data, admin_unit_id, place_id, organizer_id


@pytest.mark.parametrize("variant", ["allday", "legacy", "two_date_definitions"])
def test_events_post(client, seeder: Seeder, utils: UtilActions, app, variant):
    url, data, admin_unit_id, place_id, organizer_id = prepare_events_post_data(
        seeder, utils, variant == "legacy"
    )

    if variant == "allday":
        data["date_definitions"][0]["allday"] = "1"

    if variant == "two_date_definitions":
        data["date_definitions"].append({"start": "2021-02-07T12:00:00.000Z"})

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
        assert event.date_definitions[0].allday == (variant == "allday")

        if variant == "two_date_definitions":
            assert len(event.date_definitions) == 2
        else:
            assert len(event.date_definitions) == 1


def test_events_post_co_organizers(client, seeder: Seeder, utils: UtilActions, app, db):
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

        event = db.session.get(Event, event_id)
        assert len(event.co_organizers) == 2
        assert event.co_organizers[0].id == organizer_a_id
        assert event.co_organizers[1].id == organizer_b_id


def test_events_post_photo_no_data(client, seeder: Seeder, utils: UtilActions, app):
    url, data, admin_unit_id, place_id, organizer_id = prepare_events_post_data(
        seeder, utils
    )
    data["photo"] = {"copyright_text": "EventCally"}
    response = utils.post_json(url, data)
    utils.assert_response_unprocessable_entity(response)

    error = response.json["errors"][0]
    assert error["field"] == "photo"
    assert error["message"] == "Either image_url or image_base64 has to be defined."


def test_events_post_photo_too_small(client, seeder: Seeder, utils: UtilActions, app):
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


def test_places(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id, name="crew")
    utils.get_json_ok(url)


def test_places_post(client, seeder: Seeder, utils: UtilActions, app):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id)
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


def test_event_lists(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_api_access(user_access=False)
    event_list_id = seeder.create_event_list(admin_unit_id, name="Meine Liste")

    url = utils.get_url(
        "api_v1_organization_event_list_list", id=admin_unit_id, name="meine"
    )
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_list_id


def test_event_lists_post(client, seeder: Seeder, utils: UtilActions, app):
    _, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url("api_v1_organization_event_list_list", id=admin_unit_id)
    response = utils.post_json(
        url,
        {
            "name": "Neue Liste",
        },
    )
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import EventList

        event_list = (
            EventList.query.filter(EventList.admin_unit_id == admin_unit_id)
            .filter(EventList.name == "Neue Liste")
            .first()
        )
        assert event_list is not None
        assert event_list.name == "Neue Liste"


def test_event_lists_status(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_api_access(user_access=False)
    event_id = seeder.create_event(admin_unit_id)
    event_list_id = seeder.create_event_list(
        admin_unit_id, event_id, name="Meine Liste"
    )

    url = utils.get_url(
        "api_v1_organization_event_list_status_list",
        id=admin_unit_id,
        event_id=event_id,
        name="meine",
    )
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event_list"]["id"] == event_list_id
    assert response.json["items"][0]["contains_event"]


def test_references_incoming(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_list",
        id=admin_unit_id,
    )
    utils.get_json_ok(url)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_list",
        id=admin_unit_id,
        created_at_from="2023-07-07T00:00:00",
        created_at_to="2023-07-08T00:00:00",
    )
    utils.get_json_ok(url)


def test_references_incoming_post(client, app, seeder: Seeder, utils: UtilActions, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_list",
        id=admin_unit_id,
    )
    data = {
        "event": {"id": event_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import EventReference

        reference = db.session.get(EventReference, int(response.json["id"]))
        assert reference is not None
        assert reference.admin_unit_id == admin_unit_id
        assert reference.event_id == event_id
        assert reference.rating == 50


def test_references_incoming_post_selfReference(
    client, app, seeder: Seeder, utils: UtilActions, db
):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_list",
        id=admin_unit_id,
    )
    data = {
        "event": {"id": event_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_bad_request(response)


def test_references_outgoing(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    event_id = seeder.create_event(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_list",
        id=admin_unit_id,
        name="crew",
    )
    utils.get_json_ok(url)


def test_reference_requests_incoming(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request_list",
        id=admin_unit_id,
    )
    utils.get_json_ok(url)


def test_reference_requests_outgoing(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    seeder.create_outgoing_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request_list",
        id=admin_unit_id,
    )
    utils.get_json_ok(url)


def test_reference_requests_outgoing_post(
    client, app, seeder: Seeder, utils: UtilActions, db, mocker
):
    mail_mock = utils.mock_send_mails_async(mocker)
    user_id, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request_list",
        id=admin_unit_id,
    )
    data = {
        "event": {"id": event_id},
        "target_organization": {"id": other_admin_unit_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json
    utils.assert_send_mail_called(mail_mock, "other@test.de")

    with app.app_context():
        from project.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(
            EventReferenceRequest, int(response.json["id"])
        )
        assert reference_request is not None
        assert reference_request.admin_unit_id == other_admin_unit_id
        assert reference_request.event_id == event_id
        assert (
            reference_request.review_status == EventReferenceRequestReviewStatus.inbox
        )


def test_reference_requests_outgoing_post_autoVerify(
    client, app, seeder: Seeder, utils: UtilActions, db, mocker
):
    mail_mock = utils.mock_send_mails_async(mocker)
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_admin_unit_relation(other_admin_unit_id, admin_unit_id, True)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request_list",
        id=admin_unit_id,
    )
    data = {
        "event": {"id": event_id},
        "target_organization": {"id": other_admin_unit_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json
    utils.assert_send_mail_called(mail_mock, "other@test.de")

    with app.app_context():
        from project.models import (
            EventReference,
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(
            EventReferenceRequest, int(response.json["id"])
        )
        assert reference_request is not None
        assert reference_request.admin_unit_id == other_admin_unit_id
        assert reference_request.event_id == event_id
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.verified
        )

        reference = (
            EventReference.query.filter(
                EventReference.admin_unit_id == other_admin_unit_id
            )
            .filter(EventReference.event_id == event_id)
            .first()
        )
        assert reference is not None


def test_reference_requests_outgoing_post_foreignEvent(
    client, app, seeder: Seeder, utils: UtilActions, db
):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request_list",
        id=admin_unit_id,
    )
    data = {
        "event": {"id": event_id},
        "target_organization": {"id": other_admin_unit_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_notFound(response)


def test_reference_requests_outgoing_post_draft(
    client, app, seeder: Seeder, utils: UtilActions, db
):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    event_id = seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request_list",
        id=admin_unit_id,
    )
    data = {
        "event": {"id": event_id},
        "target_organization": {"id": other_admin_unit_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_unauthorized(response)


def test_organization_verification_requests_incoming(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access()
    seeder.create_incoming_admin_unit_verification_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request_list",
        id=admin_unit_id,
    )
    utils.get_json_ok(url)


def test_organization_verification_requests_outgoing(
    client, seeder: Seeder, utils: UtilActions
):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(api=True)
    seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_outgoing_organization_verification_request_list",
        id=unverified_admin_unit_id,
    )
    utils.get_json_ok(url)


def test_organization_verification_requests_outgoing_post(
    client, app, seeder: Seeder, utils: UtilActions, db, mocker
):
    mail_mock = utils.mock_send_mails_async(mocker)
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(api=True)

    url = utils.get_url(
        "api_v1_organization_outgoing_organization_verification_request_list",
        id=unverified_admin_unit_id,
    )
    data = {
        "target_organization": {"id": verifier_admin_unit_id},
    }

    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json
    utils.assert_send_mail_called(mail_mock, "test@test.de")

    with app.app_context():
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        organization_verification_request = db.session.get(
            AdminUnitVerificationRequest, int(response.json["id"])
        )
        assert organization_verification_request is not None
        assert (
            organization_verification_request.source_admin_unit_id
            == unverified_admin_unit_id
        )
        assert (
            organization_verification_request.target_admin_unit_id
            == verifier_admin_unit_id
        )
        assert (
            organization_verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.inbox
        )


def test_outgoing_relation_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_relation",
        id=admin_unit_id,
        target_id=other_admin_unit_id,
    )
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["id"] == relation_id
    assert response.json["source_organization"]["id"] == admin_unit_id
    assert response.json["target_organization"]["id"] == other_admin_unit_id


def test_outgoing_relation_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
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


def test_outgoing_relation_list_notAuthenticated(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
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


def test_outgoing_relation_post(client, app, seeder: Seeder, utils: UtilActions, db):
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

        relation = db.session.get(AdminUnitRelation, int(response.json["id"]))
        assert relation is not None
        assert relation.source_admin_unit_id == admin_unit_id
        assert relation.target_admin_unit_id == other_admin_unit_id
        assert relation.auto_verify_event_reference_requests


def test_outgoing_relation_post_unknownTarget(
    client, app, seeder: Seeder, utils: UtilActions
):
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


def test_outgoing_relation_post_selfReference(
    client, app, seeder: Seeder, utils: UtilActions
):
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


def test_organization_invitation_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
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


def test_organization_invitation_list_post(client, app, seeder, db, utils, mocker):
    mail_mock = utils.mock_send_mails_async(mocker)
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

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
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


def test_custom_widgets(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_custom_widget_list", id=admin_unit_id, name="mein"
    )
    utils.get_json_ok(url)


def test_custom_widgets_post(client, seeder: Seeder, utils: UtilActions, app):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url("api_v1_organization_custom_widget_list", id=admin_unit_id)
    response = utils.post_json(
        url,
        {
            "widget_type": "search",
            "name": "Neues Widget",
            "settings": {"color": "black"},
        },
    )
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.models import CustomWidget

        custom_widget = (
            CustomWidget.query.filter(CustomWidget.admin_unit_id == admin_unit_id)
            .filter(CustomWidget.name == "Neues Widget")
            .first()
        )
        assert custom_widget is not None
        assert custom_widget.widget_type == "search"
        assert custom_widget.settings["color"] == "black"
