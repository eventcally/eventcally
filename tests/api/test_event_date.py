from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.create_event(admin_unit_id)
    url = utils.get_url("api_v1_event_date", id=1)
    response = utils.get_json(url)
    utils.assert_response_ok(response)

    seeder.create_event(admin_unit_id, draft=True)
    draft_url = utils.get_url("api_v1_event_date", id=2)
    response = utils.get_json(draft_url)
    utils.assert_response_unauthorized(response)

    seeder.create_event_unverified()
    unverified_url = utils.get_url("api_v1_event_date", id=3)
    response = utils.get_json(unverified_url)
    utils.assert_response_unauthorized(response)

    seeder.create_event(admin_unit_id, planned=True)
    planned_url = utils.get_url("api_v1_event_date", id=4)
    response = utils.get_json(planned_url)
    utils.assert_response_unauthorized(response)

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(draft_url)
    utils.assert_response_ok(response)
    response = utils.get_json(planned_url)
    utils.assert_response_ok(response)


def test_read_myUnverified(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_api_access(admin_unit_verified=False)
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_date", id=1)
    response = utils.get_json(url)
    utils.assert_response_ok(response)


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url("api_v1_event_date_list")
    response = utils.get_json(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == 1


def test_search(client, seeder: Seeder, utils: UtilActions, app, db):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    start = create_berlin_date(2020, 10, 3, 10)
    event_id = seeder.create_event(admin_unit_id, start=start)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url("api_v1_event_date_search", sort="-rating")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
    assert response.json["items"][0]["start"] == "2020-10-03T10:00:00+02:00"

    url = utils.get_url("api_v1_event_date_search", keyword="name")
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", category_id=0)
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", category_id=2000)
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", weekday=1)
    response = utils.get_json_ok(url)

    url = utils.get_url(
        "api_v1_event_date_search", date_from="2020-10-03", date_to="2021-10-03"
    )
    response = utils.get_json_ok(url)

    url = utils.get_url(
        "api_v1_event_date_search", coordinate="51.9077888,10.4333312", distance=500
    )
    response = utils.get_json_ok(url)

    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    url = utils.get_url("api_v1_event_date_search", organizer_id=organizer_id)
    response = utils.get_json_ok(url)

    event_place_id = seeder.upsert_default_event_place(admin_unit_id)
    url = utils.get_url("api_v1_event_date_search", event_place_id=event_place_id)
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", admin_unit_id=admin_unit_id)
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", organization_id=admin_unit_id)
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", exclude_recurring="y")
    response = utils.get_json_ok(url)

    url = utils.get_url("api_v1_event_date_search", postal_code="38640,38690")
    response = utils.get_json_ok(url)

    listed_event_id = seeder.create_event(admin_unit_id)
    event_list_id = seeder.create_event_list(admin_unit_id, listed_event_id)
    url = utils.get_url("api_v1_event_date_search", event_list_id=event_list_id)
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == listed_event_id

    url = utils.get_url("api_v1_event_date_search", status="scheduled")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 2

    with app.app_context():
        from project.models import Event, EventStatus

        event = db.session.get(Event, event_id)
        event.status = EventStatus.cancelled
        db.session.commit()

    url = utils.get_url("api_v1_event_date_search", status="scheduled")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1

    url = utils.get_url("api_v1_event_date_search", status=["scheduled", "cancelled"])
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 2

    url = utils.get_url("api_v1_event_date_search", expected_participants_min=100)
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 0


def test_search_public_status(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    published_id = seeder.create_event(admin_unit_id)
    planned_id = seeder.create_event(admin_unit_id, planned=True)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event_date_search")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == published_id

    url = utils.get_url(
        "api_v1_event_date_search", public_status=["published", "planned"]
    )
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == published_id

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 2
    assert response.json["items"][0]["event"]["id"] == published_id
    assert response.json["items"][1]["event"]["id"] == planned_id


def test_search_oneDay(client, seeder: Seeder, utils: UtilActions):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)

    start = create_berlin_date(2020, 10, 3, 10)
    end = create_berlin_date(2020, 10, 3, 11)
    name = "Spezialveranstaltung"
    event_id = seeder.create_event(admin_unit_id, name=name, start=start, end=end)

    url = utils.get_url(
        "api_v1_event_date_search", date_from="2020-10-03", date_to="2020-10-03"
    )
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id


def test_search_is_favored(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    seeder.add_favorite_event(user_id, event_id)

    url = utils.get_url("api_v1_event_date_search")
    response = utils.get_json_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
    assert response.json["items"][0]["event"]["is_favored"]


def test_search_reference_id(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("api_v1_event_date_search")
    response = utils.get_json_ok(url, headers={"X-OrganizationId": str(admin_unit_id)})
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
    assert response.json["items"][0]["event"]["reference_id"] == reference_id

    response = utils.get_json_ok(url, headers={"X-OrganizationId": "Quatsch"})
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
    assert not response.json["items"][0]["event"]["reference_id"]

    url = utils.get_url("api_v1_event_date_search", not_referenced="y")
    response = utils.get_json_ok(url, headers={"X-OrganizationId": str(admin_unit_id)})
