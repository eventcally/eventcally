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


def _org_url(organization_id, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"/bff/public/widget/organizations/{organization_id}/event-dates?{query}"


def _org_names(response):
    return [i["event"]["name"] for i in response.json["items"]]


def test_organization_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_owner = seeder.create_user(email="other@test.de")
    other_id = seeder.create_admin_unit(other_owner, name="Andere Crew", verified=True)
    other_event_id = seeder.create_event(other_id, name="Fremd", start=START)
    seeder.create_event(admin_unit_id, name="Eigen", start=START)
    seeder.create_event(admin_unit_id, name="Draft", start=START, draft=True)
    seeder.create_event(admin_unit_id, name="Planned", start=START, planned=True)
    seeder.create_reference(other_event_id, admin_unit_id)

    response = utils.get_json_ok(_org_url(admin_unit_id, date_from="2020-10-01"))

    assert sorted(_org_names(response)) == ["Eigen", "Fremd"]
    by_name = {i["event"]["name"]: i["event"] for i in response.json["items"]}
    assert by_name["Eigen"]["organization_id"] == admin_unit_id
    assert by_name["Fremd"]["organization_id"] == other_id
    assert response.json["per_page"] == 20


def test_organization_search_excludes_planned_for_planner(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Planned", start=START, planned=True)
    seeder.create_event(admin_unit_id, name="Published", start=START)

    response = utils.get_json_ok(_org_url(admin_unit_id, date_from="2020-10-01"))

    assert _org_names(response) == ["Published"]


def test_organization_search_unverified(client, seeder, utils):
    _, admin_unit_id, _ = seeder.create_event_unverified()

    response = utils.get_json_ok(_org_url(admin_unit_id, date_from="2020-10-01"))

    assert response.json["items"] == []


def test_organization_search_filters(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Konzert", start=START, tags="music")
    seeder.create_event(admin_unit_id, name="Lesung", start=START)
    category_id = seeder.get_event_category_id("Other")

    def names(**params):
        return _org_names(
            utils.get_json_ok(_org_url(admin_unit_id, date_from="2020-10-01", **params))
        )

    assert sorted(names(keyword="Konz")) == ["Konzert"]
    assert names(tag="music") == ["Konzert"]
    assert sorted(names(category_id=0)) == ["Konzert", "Lesung"]
    assert sorted(names(category_id=category_id)) == ["Konzert", "Lesung"]
    assert names(date_to="2020-10-02") == []
    assert sorted(names(date_to="2020-10-03T12:00")) == ["Konzert", "Lesung"]


def test_organization_search_invalid_filter_falls_back_to_defaults(
    client, seeder, utils
):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Past", start=START)
    seeder.create_event(
        admin_unit_id, name="Future", start=create_berlin_date(2040, 1, 1, 10)
    )

    def names(**params):
        return _org_names(utils.get_json_ok(_org_url(admin_unit_id, **params)))

    # No date_from: today. Empty date_from: no lower bound.
    assert names() == ["Future"]
    assert sorted(names(date_from="")) == ["Future", "Past"]
    # One invalid field and the whole form is ignored, as the WTForms form was.
    assert names(date_from="garbage", keyword="Past") == ["Future"]
    assert names(date_from="2020-10-01", date_to="garbage", keyword="Past") == [
        "Future"
    ]
    assert names(date_from="2020-10-01", category_id="abc", keyword="Past") == [
        "Future"
    ]
    assert names(date_from="2020-10-01", category_id=99999, keyword="Past") == [
        "Future"
    ]


def test_organization_search_paging(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    for index in range(3):
        seeder.create_event(admin_unit_id, name=f"Event {index}", start=START)

    def get(**params):
        return utils.get_json(_org_url(admin_unit_id, date_from="2020-10-01", **params))

    body = get(per_page=2, page=2).json
    assert len(body["items"]) == 1
    assert body["total"] == 3
    assert len(get(per_page=500).json["items"]) == 3
    assert get(per_page=500).json["per_page"] == 100
    assert get(page=5).status_code == 404
    utils.assert_response_unprocessable_entity(get(page=0))


def test_organization_search_unknown_organization(client, utils):
    response = utils.get_json(_org_url(4711, date_from="2020-10-01"))

    utils.assert_response_notFound(response)
