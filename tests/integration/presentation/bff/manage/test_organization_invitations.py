BASE_URL = "/bff/manage/organizations/{}/organization-invitations"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/organization_invitation/create")


def _invitation(app, invitation_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnitInvitation

        invitation = app.extensions["sqlalchemy"].session.get(
            AdminUnitInvitation, invitation_id
        )
        return invitation and dict(
            name=invitation.admin_unit_name,
            verify=invitation.relation_verify,
            auto=invitation.relation_auto_verify_event_reference_requests,
        )


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _allow_verify_other(app, db, admin_unit_id, value=True):
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = value
        db.session.commit()


def _setup(app, db, seeder, utils, can_verify_other=True):
    _, admin_unit_id = seeder.setup_base()
    _allow_verify_other(app, db, admin_unit_id, can_verify_other)
    _shell(utils, admin_unit_id)
    return admin_unit_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)
    body = dict(email="a@test.de", admin_unit_name="Neu")

    assert utils.get_json(base).status_code == 401
    assert utils.get_json(f"{base}/create-form").status_code == 401
    assert utils.get_json(f"{base}/1").status_code == 401
    assert utils.post_json(base, body).status_code == 401
    assert utils.put_json(f"{base}/1", body).status_code == 401
    assert utils.post_json(f"{base}/1/delete", dict()).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)
    body = dict(email="a@test.de", admin_unit_name="Neu")

    assert utils.get_json(base).status_code == 403
    assert utils.get_json(f"{base}/create-form").status_code == 403
    assert utils.get_json(f"{base}/1").status_code == 403
    assert utils.post_json(base, body).status_code == 403
    assert utils.put_json(f"{base}/1", body).status_code == 403
    assert utils.post_json(f"{base}/1/delete", dict()).status_code == 403


def test_invitation_of_another_organization_is_404(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)
    other_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_id = seeder.create_admin_unit_invitation(other_id, "foreign@test.de")
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(f"{base}/{foreign_id}").status_code == 404
    assert (
        utils.put_json(f"{base}/{foreign_id}", dict(admin_unit_name="Neu")).status_code
        == 404
    )
    assert utils.post_json(f"{base}/{foreign_id}/delete", dict()).status_code == 404
    assert _invitation(app, foreign_id)["name"] == "Invited Organization"


def test_unknown_invitation_is_404(client, app, db, seeder, utils):
    base = BASE_URL.format(_setup(app, db, seeder, utils))

    assert utils.get_json(f"{base}/4711").status_code == 404
    assert utils.post_json(f"{base}/4711/delete", dict()).status_code == 404


# list


def test_list_newest_first(client, app, db, seeder, utils):
    from datetime import datetime

    from sqlalchemy import text

    admin_unit_id = _setup(app, db, seeder, utils)
    old_id = seeder.create_admin_unit_invitation(admin_unit_id, "old@test.de")
    new_id = seeder.create_admin_unit_invitation(admin_unit_id, "new@test.de")

    with app.app_context():
        for invitation_id, created_at in [
            (old_id, datetime(2026, 1, 1)),
            (new_id, datetime(2026, 2, 1)),
        ]:
            db.session.execute(
                text("UPDATE adminunitinvitation SET created_at = :c WHERE id = :id"),
                {"c": created_at, "id": invitation_id},
            )

        db.session.commit()

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert [(i["id"], i["email"]) for i in body["items"]] == [
        (new_id, "new@test.de"),
        (old_id, "old@test.de"),
    ]
    assert body["items"][0]["admin_unit_name"] == "Invited Organization"
    assert body["can_write"] is True


def test_list_out_of_range_is_404(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)

    assert utils.get_json(BASE_URL.format(admin_unit_id) + "?page=2").status_code == 404


# forms


def test_get_create_form(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id) + "/create-form").json

    assert body["id"] is None
    assert body["email"] == ""
    assert body["can_verify_other"] is True
    assert body["audit"] is None
    assert body["list_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/organization_invitations"
    )


def test_get_form(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id,
        "invited@test.de",
        "Eingeladene Crew",
        relation_auto_verify_event_reference_requests=True,
        relation_verify=True,
    )

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{invitation_id}").json

    assert body["id"] == invitation_id
    assert body["email"] == "invited@test.de"
    assert body["admin_unit_name"] == "Eingeladene Crew"
    assert body["relation_verify"] is True
    assert body["relation_auto_verify_event_reference_requests"] is True
    assert body["can_verify_other"] is True
    assert body["audit"] is not None


# create


def test_create(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)

    response = utils.post_json(
        BASE_URL.format(admin_unit_id),
        dict(
            email="invited@test.de",
            admin_unit_name="Invited Organization",
            relation_verify=True,
            relation_auto_verify_event_reference_requests=True,
        ),
    )

    assert response.status_code == 201
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/organization_invitations"
    )
    assert _invitation(app, response.json["id"]) == dict(
        name="Invited Organization", verify=True, auto=True
    )
    assert _flashes(client) == [
        ("success", "Organisationseinladung erfolgreich erstellt")
    ]

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert [m["recipient"] for m in app.test_email_service.sent_emails] == [
        "invited@test.de"
    ]


def test_create_ignores_verify_without_permission(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils, can_verify_other=False)

    response = utils.post_json(
        BASE_URL.format(admin_unit_id),
        dict(
            email="invited@test.de",
            admin_unit_name="Invited Organization",
            relation_verify=True,
        ),
    )

    assert response.status_code == 201
    assert _invitation(app, response.json["id"])["verify"] is False


def test_create_validates_email_and_name(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)
    base = BASE_URL.format(admin_unit_id)

    response = utils.post_json(base, dict(email="nope", admin_unit_name="Neu"))
    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["email"]

    response = utils.post_json(base, dict(email="a@test.de", admin_unit_name=" "))
    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["admin_unit_name"]


# update


def test_update(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{invitation_id}",
        dict(
            admin_unit_name="Renamed Organization",
            relation_verify=True,
            relation_auto_verify_event_reference_requests=True,
        ),
    )

    assert response.status_code == 200
    assert response.json["id"] == invitation_id
    assert _invitation(app, invitation_id) == dict(
        name="Renamed Organization", verify=True, auto=True
    )
    assert _flashes(client) == [
        ("success", "Organisationseinladung erfolgreich aktualisiert")
    ]


def test_update_keeps_verify_without_permission(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils, can_verify_other=False)
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id, relation_verify=True
    )

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{invitation_id}",
        dict(admin_unit_name="Renamed Organization", relation_verify=False),
    )

    assert response.status_code == 200
    assert _invitation(app, invitation_id)["verify"] is True


# delete


def test_delete(client, app, db, seeder, utils):
    admin_unit_id = _setup(app, db, seeder, utils)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{invitation_id}/delete", dict()
    )

    assert response.status_code == 200
    assert response.json == dict(message="Organisationseinladung erfolgreich gelöscht")
    assert _invitation(app, invitation_id) is None
