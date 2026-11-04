from tests.integration.presentation.bff.user.helpers import flashes, shell

MEMBERSHIPS = "/bff/user/memberships"
MEMBER_INVITATIONS = "/bff/user/member-invitations"
ORGANIZATION_INVITATIONS = "/bff/user/organization-invitations"


def _membership_id(utils, name="Meine Crew"):
    items = utils.get_json_ok(MEMBERSHIPS).json["items"]
    return next(i["id"] for i in items if i["organization_name"] == name)


def _is_member(app, member_id):
    from project.infrastructure.models import AdminUnitMember

    with app.app_context():
        return AdminUnitMember.query.get(member_id) is not None


def _invitation_exists(app, model_name, invitation_id):
    from project.infrastructure import models

    with app.app_context():
        return getattr(models, model_name).query.get(invitation_id) is not None


def _invited_user(seeder, utils):
    """The owner of `Meine Crew` and a second user who is logged in."""
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    seeder.create_user("New@Member.de")
    utils.login("New@Member.de")
    return admin_unit_id


# access


def test_anonymous_is_401(client, utils):
    for url in (
        MEMBERSHIPS,
        MEMBERSHIPS + "/1",
        MEMBER_INVITATIONS,
        MEMBER_INVITATIONS + "/1",
        ORGANIZATION_INVITATIONS,
        ORGANIZATION_INVITATIONS + "/1",
    ):
        assert utils.get_json(url).status_code == 401

    for url in (
        MEMBERSHIPS + "/1/leave",
        MEMBER_INVITATIONS + "/1/accept",
        MEMBER_INVITATIONS + "/1/decline",
        ORGANIZATION_INVITATIONS + "/1/decline",
    ):
        assert utils.post_json(url, {}).status_code == 401


def test_writes_require_csrf(client, seeder, utils):
    seeder.setup_base()

    for url in (
        MEMBERSHIPS + "/1/leave",
        MEMBER_INVITATIONS + "/1/accept",
        MEMBER_INVITATIONS + "/1/decline",
        ORGANIZATION_INVITATIONS + "/1/decline",
    ):
        assert utils.post_json(url, {}).status_code == 400


# memberships


def test_list_memberships(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    seeder.create_admin_unit(user_id, "Andere Crew")
    other_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_id, "Fremde Crew")

    body = utils.get_json_ok(MEMBERSHIPS).json

    assert sorted(i["organization_name"] for i in body["items"]) == [
        "Andere Crew",
        "Meine Crew",
    ]
    assert all(i["is_admin"] for i in body["items"])
    assert utils.get_json(MEMBERSHIPS + "?page=2").status_code == 404


def test_read_membership(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["admin"], "second@test.de")
    member_id = _membership_id(utils)

    body = utils.get_json_ok(f"{MEMBERSHIPS}/{member_id}").json

    assert body == {
        "id": member_id,
        "organization_id": admin_unit_id,
        "organization_name": "Meine Crew",
        "can_leave": True,
    }


def test_the_last_administrator_cannot_leave(client, app, seeder, utils):
    seeder.setup_base()
    shell(utils)
    member_id = _membership_id(utils)

    assert utils.get_json_ok(f"{MEMBERSHIPS}/{member_id}").json["can_leave"] is False

    response = utils.post_json(
        f"{MEMBERSHIPS}/{member_id}/leave", {"name": "Meine Crew"}
    )

    assert response.status_code == 400
    assert _is_member(app, member_id)


def test_foreign_and_unknown_memberships(client, seeder, utils):
    seeder.setup_base()
    shell(utils)
    other_id = seeder.create_user("other@test.de")
    other_unit_id = seeder.create_admin_unit(other_id, "Fremde Crew")
    foreign_id = seeder.create_admin_unit_member(other_unit_id, ["admin"], "m@test.de")

    assert utils.get_json(f"{MEMBERSHIPS}/{foreign_id}").status_code == 403
    assert (
        utils.post_json(f"{MEMBERSHIPS}/{foreign_id}/leave", {"name": "x"}).status_code
        == 403
    )
    assert utils.get_json(f"{MEMBERSHIPS}/4711").status_code == 404
    assert (
        utils.post_json(f"{MEMBERSHIPS}/4711/leave", {"name": "x"}).status_code == 404
    )


def test_leave_asks_for_the_name(client, app, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["admin"], "second@test.de")
    shell(utils)
    member_id = _membership_id(utils)

    wrong = utils.post_json(f"{MEMBERSHIPS}/{member_id}/leave", {"name": "Falsch"})
    assert wrong.status_code == 422
    assert wrong.json["errors"][0]["loc"] == ["name"]
    assert _is_member(app, member_id)

    response = utils.post_json(
        f"{MEMBERSHIPS}/{member_id}/leave", {"name": "meine crew"}
    )

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/user/organization_members"}
    assert not _is_member(app, member_id)
    assert [category for category, _ in flashes(client)] == ["success"]


# member invitations


def test_member_invitations(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    other_unit_id = seeder.create_admin_unit(owner_id, "Andere Crew")
    seeder.create_user("New@Member.de")
    utils.login("New@Member.de")
    invitation_id = seeder.create_invitation(admin_unit_id, "new@member.de")
    seeder.create_invitation(other_unit_id, "someone@else.de")

    body = utils.get_json_ok(MEMBER_INVITATIONS).json
    assert body["items"] == [
        {
            "id": invitation_id,
            "organization_id": admin_unit_id,
            "organization_name": "Meine Crew",
        }
    ]
    assert utils.get_json(MEMBER_INVITATIONS + "?page=2").status_code == 404

    assert utils.get_json_ok(f"{MEMBER_INVITATIONS}/{invitation_id}").json == (
        body["items"][0]
    )


def test_foreign_and_unknown_member_invitations(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    seeder.create_user("new@member.de")
    utils.login("new@member.de")
    shell(utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "someone@else.de")

    for action in ("", "/accept", "/decline"):
        url = f"{MEMBER_INVITATIONS}/{invitation_id}{action}"
        response = utils.get_json(url) if not action else utils.post_json(url, {})
        assert response.status_code == 403

    assert utils.get_json(f"{MEMBER_INVITATIONS}/4711").status_code == 404
    assert utils.post_json(f"{MEMBER_INVITATIONS}/4711/accept", {}).status_code == 404
    assert utils.post_json(f"{MEMBER_INVITATIONS}/4711/decline", {}).status_code == 404


def test_accept_member_invitation(client, app, seeder, utils):
    admin_unit_id = _invited_user(seeder, utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "new@member.de")
    shell(utils)

    response = utils.post_json(f"{MEMBER_INVITATIONS}/{invitation_id}/accept", {})

    assert response.status_code == 200
    assert response.json == {"redirect_url": f"/manage/admin_unit/{admin_unit_id}"}
    assert [category for category, _ in flashes(client)] == ["success"]
    assert not _invitation_exists(app, "AdminUnitMemberInvitation", invitation_id)
    assert utils.get_json_ok(MEMBERSHIPS).json["total"] == 1


def test_accept_member_invitation_with_an_unknown_role(client, seeder, utils):
    admin_unit_id = _invited_user(seeder, utils)
    invitation_id = seeder.create_invitation(
        admin_unit_id, "new@member.de", ["wrongrole"]
    )
    shell(utils)

    response = utils.post_json(f"{MEMBER_INVITATIONS}/{invitation_id}/accept", {})

    assert response.status_code == 200
    assert response.json == {"redirect_url": f"/manage/admin_unit/{admin_unit_id}"}


def test_accepting_with_a_requested_deletion_only_flashes(
    client, app, db, seeder, utils
):
    import datetime

    from project.infrastructure.models import User

    admin_unit_id = _invited_user(seeder, utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "new@member.de")
    shell(utils)

    with app.app_context():
        user = User.query.filter(User.email == "New@Member.de").one()
        user.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()

    response = utils.post_json(f"{MEMBER_INVITATIONS}/{invitation_id}/accept", {})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/profile"}
    assert [category for category, _ in flashes(client)] == ["danger"]
    assert _invitation_exists(app, "AdminUnitMemberInvitation", invitation_id)


def test_decline_member_invitation(client, app, seeder, utils):
    admin_unit_id = _invited_user(seeder, utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "new@member.de")
    shell(utils)

    response = utils.post_json(f"{MEMBER_INVITATIONS}/{invitation_id}/decline", {})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/manage"}
    assert [category for category, _ in flashes(client)] == ["success"]
    assert not _invitation_exists(app, "AdminUnitMemberInvitation", invitation_id)
    assert utils.get_json_ok(MEMBERSHIPS).json["total"] == 0


# organization invitations


def test_organization_invitations(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    other_unit_id = seeder.create_admin_unit(owner_id, "Andere Crew")
    seeder.create_user("New@Member.de")
    utils.login("New@Member.de")
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id, "new@member.de", admin_unit_name="Neue Crew"
    )
    seeder.create_admin_unit_invitation(other_unit_id, "someone@else.de")

    body = utils.get_json_ok(ORGANIZATION_INVITATIONS).json
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["id"] == invitation_id
    assert item["organization_name"] == "Meine Crew"
    assert item["name"] == "Neue Crew"
    assert item["created_at"] is not None
    assert utils.get_json(ORGANIZATION_INVITATIONS + "?page=2").status_code == 404

    assert utils.get_json_ok(f"{ORGANIZATION_INVITATIONS}/{invitation_id}").json == item


def test_foreign_and_unknown_organization_invitations(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    seeder.create_user("new@member.de")
    utils.login("new@member.de")
    shell(utils)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id, "other@test.de")

    url = f"{ORGANIZATION_INVITATIONS}/{invitation_id}"
    assert utils.get_json(url).status_code == 403
    assert utils.post_json(url + "/decline", {}).status_code == 403
    assert utils.get_json(f"{ORGANIZATION_INVITATIONS}/4711").status_code == 404
    assert (
        utils.post_json(f"{ORGANIZATION_INVITATIONS}/4711/decline", {}).status_code
        == 404
    )


def test_decline_organization_invitation(client, app, seeder, utils):
    admin_unit_id = _invited_user(seeder, utils)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id, "new@member.de")
    shell(utils)

    response = utils.post_json(
        f"{ORGANIZATION_INVITATIONS}/{invitation_id}/decline", {}
    )

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/user/organization_invitations"}
    assert [category for category, _ in flashes(client)] == ["success"]
    assert not _invitation_exists(app, "AdminUnitInvitation", invitation_id)
