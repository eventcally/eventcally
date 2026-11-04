import pytest

from project.shared.dateutils import create_berlin_date

CREATE_URL = "/bff/manage/organizations/{}/event-references"
ITEM_URL = "/bff/manage/event-references/{}"
START = create_berlin_date(2030, 10, 3, 10)


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/custom-widgets")


def _other_event(seeder, name="Fremd"):
    owner_id = seeder.create_user(email="other@test.de")
    other_id = seeder.create_admin_unit(owner_id, name="Andere Crew", verified=True)
    return other_id, seeder.create_event(other_id, name=name, start=START)


def _references(app, admin_unit_id):
    with app.app_context():
        from project.infrastructure.models import EventReference

        return [
            r.event_id
            for r in EventReference.query.filter_by(admin_unit_id=admin_unit_id).all()
        ]


def test_anonymous_is_401(client, seeder, utils):
    _, event_id = _other_event(seeder)

    assert (
        utils.post_json(CREATE_URL.format(1), {"event_id": event_id}).status_code == 401
    )
    assert utils.delete(ITEM_URL.format(1)).status_code == 401


def test_create(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    _, event_id = _other_event(seeder)

    response = utils.post_json(CREATE_URL.format(admin_unit_id), {"event_id": event_id})

    assert response.status_code == 201
    assert response.json["id"]
    assert _references(app, admin_unit_id) == [event_id]


def test_create_own_event_is_rejected(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    event_id = seeder.create_event(admin_unit_id, name="Eigen", start=START)

    response = utils.post_json(CREATE_URL.format(admin_unit_id), {"event_id": event_id})

    assert response.status_code in (400, 422)
    assert _references(app, admin_unit_id) == []


def test_create_for_foreign_organization_is_403(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    other_id, event_id = _other_event(seeder)

    response = utils.post_json(CREATE_URL.format(other_id), {"event_id": event_id})

    assert response.status_code == 403


def test_create_unknown_event_is_rejected(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.post_json(CREATE_URL.format(admin_unit_id), {"event_id": 4711})

    assert response.status_code == 400
    assert response.json["name"] == "NotFoundError"


def test_delete(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    _, event_id = _other_event(seeder)
    reference_id = seeder.create_reference(event_id, admin_unit_id)

    response = utils.delete(ITEM_URL.format(reference_id))

    assert response.status_code == 204
    assert _references(app, admin_unit_id) == []


def test_delete_foreign_reference_is_403(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    other_id, event_id = _other_event(seeder)
    reference_id = seeder.create_reference(event_id, other_id)

    assert utils.delete(ITEM_URL.format(reference_id)).status_code == 403
    assert _references(app, other_id) == [event_id]


def test_delete_unknown_is_rejected(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.delete(ITEM_URL.format(4711))

    assert response.status_code == 400
    assert response.json["name"] == "NotFoundError"


# The incoming / outgoing reference pages

LIST_URL = "/bff/manage/organizations/{}/incoming-event-references"
OUTGOING_URL = "/bff/manage/organizations/{}/outgoing-event-references"
READ_URL = "/bff/manage/organizations/{}/incoming-event-references/{}"


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _set(app, db, reference_id, **values):
    from sqlalchemy import text

    columns = ", ".join(f"{key} = :{key}" for key in values)
    with app.app_context():
        db.session.execute(
            text(f"UPDATE eventreference SET {columns} WHERE id = :id"),
            dict(values, id=reference_id),
        )
        db.session.commit()


def _rating(app, db, reference_id):
    with app.app_context():
        from project.infrastructure.models import EventReference

        return db.session.get(EventReference, reference_id).rating


def _exists(app, db, reference_id):
    with app.app_context():
        from project.infrastructure.models import EventReference

        return db.session.get(EventReference, reference_id) is not None


@pytest.fixture
def incoming(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _, other_admin_unit_id, event_id, reference_id = seeder.create_any_reference(
        admin_unit_id
    )
    _shell(utils, admin_unit_id)
    return admin_unit_id, other_admin_unit_id, event_id, reference_id


def test_incoming_pages_are_401_for_anonymous(client, utils):
    assert utils.get_json(LIST_URL.format(1)).status_code == 401
    assert utils.get_json(OUTGOING_URL.format(1)).status_code == 401
    assert utils.get_json(READ_URL.format(1, 1)).status_code == 401
    assert utils.put_json(READ_URL.format(1, 1), {"rating": 50}).status_code == 401
    assert utils.post_json(READ_URL.format(1, 1) + "/delete", {}).status_code == 401


def test_incoming_pages_without_permission_are_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")
    base = READ_URL.format(admin_unit_id, 1)

    assert utils.get_json(LIST_URL.format(admin_unit_id)).status_code == 403
    assert utils.get_json(OUTGOING_URL.format(admin_unit_id)).status_code == 403
    assert utils.get_json(base).status_code == 403
    assert utils.put_json(base, {"rating": 50}).status_code == 403
    assert utils.post_json(base + "/delete", {}).status_code == 403


def test_incoming_list(app, db, seeder, utils, incoming):
    admin_unit_id, other_admin_unit_id, event_id, older_id = incoming
    newer_event_id = seeder.create_event(other_admin_unit_id, name="Neues Event")
    newer_id = seeder.create_reference(newer_event_id, admin_unit_id)
    _set(app, db, older_id, created_at="2026-01-01", rating=70)
    _set(app, db, newer_id, created_at="2026-02-01")

    response = utils.get_json(LIST_URL.format(admin_unit_id))

    assert response.status_code == 200
    assert response.json["can_write"] is True
    assert response.json["per_page"] == 50
    assert response.json["total"] == 2
    assert [i["id"] for i in response.json["items"]] == [newer_id, older_id]
    item = response.json["items"][1]
    assert item["event_id"] == event_id
    assert item["event_name"] == "Name"
    assert item["organization_id"] == other_admin_unit_id
    assert item["organization_name"] == "Other Crew"
    assert item["rating"] == 70
    assert item["created_at"].startswith("2026-01-01")
    choices = response.json["rating_choices"]
    assert choices[0] == {"value": 0, "label": "0 (Wenig relevant)"}
    assert choices[5] == {"value": 50, "label": "5 (Standard)"}


def test_incoming_list_out_of_range_is_404(client, utils, incoming):
    admin_unit_id, *_ = incoming

    assert utils.get_json(LIST_URL.format(admin_unit_id) + "?page=3").status_code == 404


def test_outgoing_list(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id, name="Mein Event")
    other_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Andere Crew"
    )
    reference_id = seeder.create_reference(event_id, other_id)

    response = utils.get_json(OUTGOING_URL.format(admin_unit_id))

    assert response.status_code == 200
    assert response.json["can_write"] is False
    assert [
        (i["id"], i["event_name"], i["organization_id"], i["organization_name"])
        for i in response.json["items"]
    ] == [(reference_id, "Mein Event", other_id, "Andere Crew")]

    assert (
        utils.get_json(OUTGOING_URL.format(admin_unit_id) + "?page=2").status_code
        == 404
    )


def test_read(app, db, utils, incoming):
    admin_unit_id, _, event_id, reference_id = incoming
    _set(app, db, reference_id, rating=70)

    response = utils.get_json(READ_URL.format(admin_unit_id, reference_id))

    assert response.status_code == 200
    assert response.json["id"] == reference_id
    assert response.json["event_id"] == event_id
    assert response.json["event_name"] == "Name"
    assert response.json["rating"] == 70
    assert response.json["rating_text"] == "7/10"
    assert response.json["can_write"] is True
    assert response.json["audit"]["created_at"]
    assert len(response.json["rating_choices"]) == 11


def test_read_without_rating_has_no_rating_text(app, db, utils, incoming):
    admin_unit_id, _, _, reference_id = incoming
    _set(app, db, reference_id, rating=0)

    response = utils.get_json(READ_URL.format(admin_unit_id, reference_id))

    assert response.json["rating"] == 0
    assert response.json["rating_text"] is None


def test_read_of_another_organization_or_unknown_is_404(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _, _, _, reference_id = seeder.create_any_reference(admin_unit_id)
    # The same user manages a second organization: the reference is not its own.
    second_id = seeder.create_admin_unit(user_id, "Zweite Crew")
    _shell(utils, admin_unit_id)

    assert utils.get_json(READ_URL.format(admin_unit_id, 4711)).status_code == 404
    assert utils.get_json(READ_URL.format(second_id, reference_id)).status_code == 404
    assert (
        utils.put_json(
            READ_URL.format(second_id, reference_id), {"rating": 70}
        ).status_code
        == 404
    )
    assert (
        utils.post_json(
            READ_URL.format(second_id, reference_id) + "/delete", {}
        ).status_code
        == 404
    )


def test_update_rating(app, db, client, utils, incoming):
    admin_unit_id, _, _, reference_id = incoming

    response = utils.put_json(
        READ_URL.format(admin_unit_id, reference_id), {"rating": 70}
    )

    assert response.status_code == 200
    assert response.json["message"] == "Eingehende Empfehlung erfolgreich aktualisiert"
    assert _rating(app, db, reference_id) == 70


def test_update_rating_rejects_an_unknown_value(app, db, utils, incoming):
    admin_unit_id, _, _, reference_id = incoming

    response = utils.put_json(
        READ_URL.format(admin_unit_id, reference_id), {"rating": 55}
    )

    assert response.status_code == 422
    assert _rating(app, db, reference_id) != 55


def test_update_rating_db_error_is_400(app, db, utils, mocker, incoming):
    admin_unit_id, _, _, reference_id = incoming
    utils.mock_db_commit(mocker)

    response = utils.put_json(
        READ_URL.format(admin_unit_id, reference_id), {"rating": 70}
    )

    assert response.status_code == 400
    assert response.json["name"] == "InfrastructureError"


def test_update_of_unknown_reference_is_404(client, utils, incoming):
    admin_unit_id, *_ = incoming

    assert (
        utils.put_json(READ_URL.format(admin_unit_id, 4711), {"rating": 70}).status_code
        == 404
    )


def test_delete_flashes_and_answers_the_list(app, db, client, utils, incoming):
    admin_unit_id, _, _, reference_id = incoming

    response = utils.post_json(
        READ_URL.format(admin_unit_id, reference_id) + "/delete", {}
    )

    assert response.status_code == 200
    assert response.json["message"] == "Eingehende Empfehlung erfolgreich gelöscht"
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/incoming_event_references"
    )
    assert _flashes(client) == [
        ("success", "Eingehende Empfehlung erfolgreich gelöscht")
    ]
    assert not _exists(app, db, reference_id)


def test_delete_inline_does_not_flash(app, db, client, utils, incoming):
    admin_unit_id, _, _, reference_id = incoming

    response = utils.post_json(
        READ_URL.format(admin_unit_id, reference_id) + "/delete", {"inline": True}
    )

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert not session.get("_flashes")
    assert not _exists(app, db, reference_id)


def test_delete_db_error_is_400(app, db, utils, mocker, incoming):
    admin_unit_id, _, _, reference_id = incoming
    utils.mock_db_commit(mocker)

    response = utils.post_json(
        READ_URL.format(admin_unit_id, reference_id) + "/delete", {}
    )

    assert response.status_code == 400
    assert response.json["name"] == "InfrastructureError"


def test_delete_of_unknown_reference_is_404(client, utils, incoming):
    admin_unit_id, *_ = incoming

    assert (
        utils.post_json(
            READ_URL.format(admin_unit_id, 4711) + "/delete", {}
        ).status_code
        == 404
    )
