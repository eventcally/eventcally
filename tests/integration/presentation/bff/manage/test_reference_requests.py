import pytest

INCOMING_URL = "/bff/manage/organizations/{}/incoming-event-reference-requests"
OUTGOING_URL = "/bff/manage/organizations/{}/outgoing-event-reference-requests"


def _set(app, db, request_id, **values):
    from sqlalchemy import text

    columns = ", ".join(f"{key} = :{key}" for key in values)
    with app.app_context():
        db.session.execute(
            text(f"UPDATE eventreferencerequest SET {columns} WHERE id = :id"),
            dict(values, id=request_id),
        )
        db.session.commit()


@pytest.fixture
def incoming(app, db, seeder):
    """Two requests to the organization: an older rejected and a newer inbox one."""
    _, admin_unit_id = seeder.setup_base()
    other_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Andere Crew"
    )
    older_id = seeder.create_reference_request(
        seeder.create_event(other_id, name="Altes Event"), admin_unit_id
    )
    newer_id = seeder.create_reference_request(
        seeder.create_event(other_id, name="Neues Event"), admin_unit_id
    )
    _set(app, db, older_id, created_at="2026-01-01", review_status=3)
    _set(app, db, newer_id, created_at="2026-02-01")
    return admin_unit_id, other_id, older_id, newer_id


def test_anonymous_is_401(client, utils):
    assert utils.get_json(INCOMING_URL.format(1)).status_code == 401
    assert utils.get_json(OUTGOING_URL.format(1)).status_code == 401
    assert utils.get_json(OUTGOING_URL.format(1) + "/1").status_code == 401


def test_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    assert utils.get_json(INCOMING_URL.format(admin_unit_id)).status_code == 403
    assert utils.get_json(OUTGOING_URL.format(admin_unit_id)).status_code == 403
    assert utils.get_json(OUTGOING_URL.format(admin_unit_id) + "/1").status_code == 403


def test_incoming_list(utils, incoming):
    admin_unit_id, other_id, older_id, newer_id = incoming

    response = utils.get_json(INCOMING_URL.format(admin_unit_id))

    assert response.status_code == 200
    assert response.json["can_write"] is True
    assert response.json["per_page"] == 50
    assert [i["id"] for i in response.json["items"]] == [newer_id, older_id]
    newer, older = response.json["items"]
    assert newer["event_name"] == "Neues Event"
    assert newer["organization_id"] == other_id
    assert newer["organization_name"] == "Andere Crew"
    assert newer["review_status"] == 1
    assert newer["review_status_label"] == "Ungeprüft"
    assert newer["created_at"].startswith("2026-02-01")
    assert newer["can_review"] is True
    assert older["review_status_label"] == "Abgelehnt"
    assert older["can_review"] is True
    assert response.json["review_status_choices"] == [
        {"value": -1, "label": "Alle"},
        {"value": 1, "label": "Ungeprüft"},
        {"value": 2, "label": "Verifiziert"},
        {"value": 3, "label": "Abgelehnt"},
    ]


def test_incoming_list_cannot_review_a_verified_request(app, db, utils, incoming):
    admin_unit_id, _, older_id, newer_id = incoming
    _set(app, db, newer_id, review_status=2)

    items = utils.get_json(INCOMING_URL.format(admin_unit_id)).json["items"]

    assert [(i["id"], i["can_review"]) for i in items] == [
        (newer_id, False),
        (older_id, True),
    ]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("?review_status=3", ["older"]),
        ("?review_status=1", ["newer"]),
        ("?review_status=-1", ["newer", "older"]),
        ("?review_status=99", ["newer", "older"]),
        ("", ["newer", "older"]),
    ],
)
def test_incoming_list_filters_by_review_status(utils, incoming, query, expected):
    admin_unit_id, _, older_id, newer_id = incoming
    ids = {"older": older_id, "newer": newer_id}

    response = utils.get_json(INCOMING_URL.format(admin_unit_id) + query)

    assert [i["id"] for i in response.json["items"]] == [ids[e] for e in expected]


def test_incoming_list_out_of_range_is_404(utils, incoming):
    admin_unit_id, *_ = incoming

    assert (
        utils.get_json(INCOMING_URL.format(admin_unit_id) + "?page=3").status_code
        == 404
    )


@pytest.fixture
def outgoing(app, db, seeder):
    _, admin_unit_id = seeder.setup_base()
    _, other_id, event_id, request_id = seeder.create_outgoing_reference_request(
        admin_unit_id
    )
    return admin_unit_id, other_id, event_id, request_id


def test_outgoing_list(utils, outgoing):
    admin_unit_id, other_id, event_id, request_id = outgoing

    response = utils.get_json(OUTGOING_URL.format(admin_unit_id))

    assert response.status_code == 200
    assert response.json["can_write"] is False
    assert [
        (i["id"], i["event_id"], i["organization_id"], i["organization_name"])
        for i in response.json["items"]
    ] == [(request_id, event_id, other_id, "Other Crew")]
    assert response.json["items"][0]["can_review"] is False

    filtered = utils.get_json(OUTGOING_URL.format(admin_unit_id) + "?review_status=3")
    assert filtered.json["items"] == []
    assert (
        utils.get_json(OUTGOING_URL.format(admin_unit_id) + "?page=2").status_code
        == 404
    )


def test_outgoing_read(app, db, utils, outgoing):
    admin_unit_id, other_id, event_id, request_id = outgoing
    _set(app, db, request_id, review_status=3, rejection_reason=4)

    response = utils.get_json(OUTGOING_URL.format(admin_unit_id) + f"/{request_id}")

    assert response.status_code == 200
    assert response.json["id"] == request_id
    assert response.json["event_id"] == event_id
    assert response.json["event_name"] == "Name"
    assert response.json["review_status"] == 3
    assert response.json["review_status_label"] == "Abgelehnt"
    assert response.json["rejection_reason_label"]
    assert response.json["organization_id"] == other_id
    assert response.json["organization_name"] == "Other Crew"
    assert response.json["audit"]["created_at"]


def test_outgoing_read_without_rejection_reason(utils, outgoing):
    admin_unit_id, _, _, request_id = outgoing

    response = utils.get_json(OUTGOING_URL.format(admin_unit_id) + f"/{request_id}")

    assert response.json["review_status_label"] == "Ungeprüft"
    assert response.json["rejection_reason_label"] is None


def test_outgoing_read_of_another_organization_or_unknown_is_404(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _, _, _, request_id = seeder.create_outgoing_reference_request(admin_unit_id)
    # The same user manages a second organization: the request is not its own.
    second_id = seeder.create_admin_unit(user_id, "Zweite Crew")

    assert (
        utils.get_json(OUTGOING_URL.format(second_id) + f"/{request_id}").status_code
        == 404
    )
    assert (
        utils.get_json(OUTGOING_URL.format(admin_unit_id) + "/4711").status_code == 404
    )
