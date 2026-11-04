import pytest

BASE_URL = "/bff/manage/organizations/{}/members"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/organization_members")


def _own_member_id(app, admin_unit_id, user_id):
    with app.app_context():
        from project.infrastructure.seed_helpers import (
            get_member_for_admin_unit_by_user_id,
        )

        return get_member_for_admin_unit_by_user_id(admin_unit_id, user_id).id


def _role_names(app, member_id):
    with app.app_context():
        from project.infrastructure.seed_helpers import get_admin_unit_member

        member = get_admin_unit_member(member_id)
        return member and sorted(role.name for role in member.roles)


@pytest.fixture
def setup(client, app, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    member_id = seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier"], "member@test.de"
    )
    _shell(utils, admin_unit_id)
    return user_id, admin_unit_id, member_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 401
    assert utils.put_json(f"{base}/1", dict(roles=[])).status_code == 401
    assert utils.post_json(f"{base}/1/delete", dict()).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 403
    assert utils.put_json(f"{base}/{member_id}", dict(roles=[])).status_code == 403
    assert utils.post_json(f"{base}/{member_id}/delete", dict()).status_code == 403


def test_member_of_another_organization_is_404(client, app, seeder, utils, setup):
    user_id, admin_unit_id, _ = setup
    other_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_member_id = seeder.create_admin_unit_member(
        other_id, ["event_verifier"], "foreign@test.de"
    )
    base = BASE_URL.format(admin_unit_id)

    response = utils.put_json(f"{base}/{foreign_member_id}", dict(roles=["admin"]))
    assert response.status_code == 404
    assert utils.post_json(
        f"{base}/{foreign_member_id}/delete", dict()
    ).status_code == (404)
    assert _role_names(app, foreign_member_id) == ["event_verifier"]


def test_unknown_member_is_404(client, utils, setup):
    _, admin_unit_id, _ = setup
    base = BASE_URL.format(admin_unit_id)

    assert utils.put_json(f"{base}/4711", dict(roles=[])).status_code == 404
    assert utils.post_json(f"{base}/4711/delete", dict()).status_code == 404


# list


def test_list(client, app, seeder, utils, setup):
    user_id, admin_unit_id, member_id = setup
    seeder.create_admin_unit_member(admin_unit_id, ["admin"], "Alpha@test.de")

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert [item["email"] for item in body["items"]] == [
        "Alpha@test.de",
        "member@test.de",
        "test@test.de",
    ]
    alpha, member, own = body["items"]
    assert alpha["roles"] == [dict(name="admin", title="Administrator:in")]
    assert member["roles"] == [
        dict(name="event_verifier", title="Veranstaltungsexpert:in")
    ]
    assert member["is_current_user"] is False
    assert member["leave_url"] is None
    assert own["is_current_user"] is True
    own_id = _own_member_id(app, admin_unit_id, user_id)
    assert own["id"] == own_id
    assert own["leave_url"] == f"/user/organization_member/{own_id}/delete"
    assert [c["name"] for c in body["role_choices"]] == ["admin", "event_verifier"]
    assert body["total"] == 3
    assert body["can_write"] is True
    assert body["can_invite"] is True


def test_list_out_of_range_is_404(client, utils, setup):
    _, admin_unit_id, _ = setup

    assert utils.get_json(BASE_URL.format(admin_unit_id) + "?page=2").status_code == 404


# update


def test_update_roles(client, app, utils, setup):
    _, admin_unit_id, member_id = setup

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{member_id}", dict(roles=["admin"])
    )

    assert response.status_code == 200
    assert response.json == dict(message="Mitglied erfolgreich aktualisiert")
    assert _role_names(app, member_id) == ["admin"]


def test_update_own_roles_is_allowed(client, app, utils, setup):
    user_id, admin_unit_id, _ = setup
    own_id = _own_member_id(app, admin_unit_id, user_id)

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{own_id}", dict(roles=["event_verifier"])
    )

    assert response.status_code == 200
    assert "event_verifier" in _role_names(app, own_id)


def test_update_unknown_role_is_a_field_error(client, app, utils, setup):
    _, admin_unit_id, member_id = setup

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{member_id}", dict(roles=["boss"])
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["roles"]
    assert response.json["errors"][0]["msg"] == "Keine gültige Auswahl"
    assert _role_names(app, member_id) == ["event_verifier"]


# delete


def test_delete(client, app, utils, setup):
    _, admin_unit_id, member_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{member_id}/delete", dict()
    )

    assert response.status_code == 200
    assert response.json == dict(message="Mitglied erfolgreich gelöscht")
    assert _role_names(app, member_id) is None


def test_delete_own_membership_is_403(client, app, utils, setup):
    user_id, admin_unit_id, _ = setup
    own_id = _own_member_id(app, admin_unit_id, user_id)

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{own_id}/delete", dict()
    )

    assert response.status_code == 403
    assert _role_names(app, own_id) is not None
