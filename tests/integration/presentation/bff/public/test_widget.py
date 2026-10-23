import pytest

from project.shared.dateutils import create_berlin_date

DATES_URL = "/bff/public/widget/event-dates"
CATEGORIES_URL = "/bff/public/widget/categories"
START = create_berlin_date(2020, 10, 3, 10)


def _url(**params):
    query = dict(date_from="2020-10-01")
    query.update(params)
    return DATES_URL + "?" + "&".join(f"{k}={v}" for k, v in query.items())


def _names(response):
    return sorted(i["event"]["name"] for i in response.json["items"])


def test_anonymous_can_search(client, seeder, utils):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, verified=True)
    seeder.create_event(admin_unit_id, name="Published", start=START)
    seeder.create_event(admin_unit_id, name="Draft", start=START, draft=True)
    seeder.create_event(admin_unit_id, name="Planned", start=START, planned=True)

    response = utils.get_json_ok(_url())

    assert _names(response) == ["Published"]
    item = response.json["items"][0]
    assert item["allday"] is False
    assert item["event"]["organization_name"] == "Meine Crew"
    assert item["event"]["organizer_name"]
    assert item["event"]["place_name"]
    assert item["event"]["public_status"] == "published"
    assert item["event"]["description_preview"] == "Beschreibung"
    assert item["event"]["photo"] is None
    assert response.json["total"] == 1
    assert response.json["per_page"] == 10


def test_filters(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_owner = seeder.create_user(email="other@test.de")
    other_id = seeder.create_admin_unit(other_owner, name="Andere Crew", verified=True)
    seeder.create_event(admin_unit_id, name="Konzert", start=START)
    seeder.create_event(admin_unit_id, name="Lesung", start=START)
    seeder.create_event(other_id, name="Fremd", start=START)
    seeder.create_event(
        admin_unit_id, name="Spaet", start=create_berlin_date(2020, 11, 20, 10)
    )

    assert _names(utils.get_json_ok(_url(organization_id=admin_unit_id))) == [
        "Konzert",
        "Lesung",
        "Spaet",
    ]
    assert _names(utils.get_json_ok(_url(keyword="Konz"))) == ["Konzert"]
    assert _names(utils.get_json_ok(_url(date_to="2020-10-03"))) == [
        "Fremd",
        "Konzert",
        "Lesung",
    ]
    assert _names(utils.get_json_ok(_url(category_id=0))) != []


def test_paging(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    for index in range(3):
        seeder.create_event(admin_unit_id, name=f"Event {index}", start=START)

    body = utils.get_json_ok(_url(per_page=2, page=2)).json

    assert len(body["items"]) == 1
    assert body["total"] == 3
    assert body["pages"] == 2


@pytest.mark.parametrize("params", [dict(per_page=51), dict(per_page=0), dict(page=0)])
def test_invalid_paging_is_422(client, utils, params):
    utils.assert_response_unprocessable_entity(utils.get_json(_url(**params)))


def test_date_from_is_required(client, utils):
    utils.assert_response_unprocessable_entity(utils.get_json(DATES_URL))


def test_description_is_plain_text(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(
        admin_unit_id,
        name="Event",
        start=START,
        description="<p>Hallo <b>Welt</b><script>alert(1)</script></p>",
    )

    preview = utils.get_json_ok(_url()).json["items"][0]["event"]["description_preview"]

    assert "<" not in preview
    assert preview.startswith("Hallo Welt")


def test_categories(client, utils):
    body = utils.get_json_ok(CATEGORIES_URL).json

    names = [c["name"] for c in body["items"]]
    assert names and names == sorted(names)
    assert all(isinstance(c["id"], int) for c in body["items"])


def test_photo(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, name="Event", start=START)
    seeder.assign_image_to_event(event_id, seeder.upsert_default_image())

    photo = utils.get_json_ok(_url()).json["items"][0]["event"]["photo"]

    assert "s=200" in photo["url_200"]
    assert "s=500" in photo["url_500"]
    assert "copyright_text" in photo
    assert "license_code" in photo
