import datetime

import pytest

BASE_URL = "/bff/manage/organizations/{}/deletion"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/request-deletion")


def _requested_at(app, db, admin_unit_id, set_to="unchanged"):
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)

        if set_to != "unchanged":
            admin_unit.deletion_requested_at = set_to
            db.session.commit()

        return admin_unit.deletion_requested_at


@pytest.fixture
def setup(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    return admin_unit_id


# access


@pytest.mark.parametrize("suffix", ["", "/cancel"])
def test_anonymous_is_401(client, seeder, utils, suffix):
    owner_id = seeder.create_user()
    base = BASE_URL.format(seeder.create_admin_unit(owner_id)) + suffix

    assert utils.post_json(base, dict(name="Meine Crew")).status_code == 401


@pytest.mark.parametrize("suffix", ["", "/cancel"])
def test_member_without_permission_is_403(client, seeder, utils, suffix):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id) + suffix

    assert utils.post_json(base, dict(name="Meine Crew")).status_code == 403


@pytest.mark.parametrize("suffix", ["", "/cancel"])
def test_unknown_organization_is_404(client, seeder, utils, suffix):
    seeder.create_user(admin=True)
    utils.login()
    utils.get_ok("/organizations")

    response = utils.post_json(BASE_URL.format(9999) + suffix, dict(name="x"))

    assert response.status_code == 404


def test_post_requires_csrf(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    response = utils.post_json(BASE_URL.format(admin_unit_id), dict(name="Meine Crew"))

    assert response.status_code == 400


# request


def test_request_deletion(client, app, db, setup, utils):
    admin_unit_id = setup

    response = utils.post_json(BASE_URL.format(admin_unit_id), dict(name="meine crew"))

    assert response.status_code == 200
    assert response.json["redirect_url"] == f"/manage/admin_unit/{admin_unit_id}"
    assert _requested_at(app, db, admin_unit_id) is not None

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert (
        app.test_email_service.sent_emails[0]["subject"]
        == "Löschung der Organisation beantragt"
    )


def test_request_deletion_name_mismatch(client, app, db, setup, utils):
    admin_unit_id = setup

    response = utils.post_json(BASE_URL.format(admin_unit_id), dict(name="wrong"))

    assert response.status_code == 422
    error = response.json["errors"][0]
    assert error["loc"][-1] == "name"
    assert (
        error["msg"]
        == "Der eingegebene Name entspricht nicht dem Namen der Organisation"
    )
    assert _requested_at(app, db, admin_unit_id) is None


def test_request_deletion_needs_a_name(client, setup, utils):
    response = utils.post_json(BASE_URL.format(setup), dict(name=""))

    assert response.status_code == 422


def test_request_deletion_twice_is_400(client, app, db, setup, utils):
    admin_unit_id = setup
    _requested_at(app, db, admin_unit_id, datetime.datetime.now(datetime.UTC))

    response = utils.post_json(BASE_URL.format(admin_unit_id), dict(name="Meine Crew"))

    assert response.status_code == 400


def test_request_deletion_db_error_is_400(client, app, db, setup, utils, mocker):
    admin_unit_id = setup
    utils.mock_db_commit(mocker)

    response = utils.post_json(BASE_URL.format(admin_unit_id), dict(name="Meine Crew"))

    assert response.status_code == 400
    assert _requested_at(app, db, admin_unit_id) is None


# cancel


def test_cancel_deletion(client, app, db, setup, utils):
    admin_unit_id = setup
    _requested_at(app, db, admin_unit_id, datetime.datetime.now(datetime.UTC))

    response = utils.post_json(
        BASE_URL.format(admin_unit_id) + "/cancel", dict(name="Meine Crew")
    )

    assert response.status_code == 200
    assert response.json["redirect_url"] == f"/manage/admin_unit/{admin_unit_id}"
    assert _requested_at(app, db, admin_unit_id) is None


def test_cancel_deletion_name_mismatch(client, app, db, setup, utils):
    admin_unit_id = setup
    _requested_at(app, db, admin_unit_id, datetime.datetime.now(datetime.UTC))

    response = utils.post_json(
        BASE_URL.format(admin_unit_id) + "/cancel", dict(name="wrong")
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"][-1] == "name"
    assert _requested_at(app, db, admin_unit_id) is not None


def test_cancel_deletion_without_request_is_400(client, setup, utils):
    response = utils.post_json(
        BASE_URL.format(setup) + "/cancel", dict(name="Meine Crew")
    )

    assert response.status_code == 400
