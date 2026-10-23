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
