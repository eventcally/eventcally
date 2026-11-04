BASE_URL = "/bff/manage/organizations/{}/member-invitations"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(
        f"/manage/admin_unit/{admin_unit_id}/organization_member_invitation/create"
    )


def _invitation(app, invitation_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnitMemberInvitation

        invitation = app.extensions["sqlalchemy"].session.get(
            AdminUnitMemberInvitation, invitation_id
        )
        return invitation and invitation.roles


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _setup(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    return admin_unit_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 401
    assert utils.get_json(f"{base}/create-form").status_code == 401
    assert utils.post_json(base, dict(email="a@test.de")).status_code == 401
    assert utils.put_json(f"{base}/1", dict(roles=[])).status_code == 401
    assert utils.post_json(f"{base}/1/delete", dict()).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 403
    assert utils.get_json(f"{base}/create-form").status_code == 403
    assert utils.post_json(base, dict(email="a@test.de")).status_code == 403
    assert utils.put_json(f"{base}/1", dict(roles=[])).status_code == 403
    assert utils.post_json(f"{base}/1/delete", dict()).status_code == 403


def test_invitation_of_another_organization_is_404(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    other_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_id = seeder.create_invitation(other_id, "foreign@test.de", ["admin"])
    base = BASE_URL.format(admin_unit_id)

    assert utils.put_json(f"{base}/{foreign_id}", dict(roles=[])).status_code == 404
    assert utils.post_json(f"{base}/{foreign_id}/delete", dict()).status_code == 404
    assert _invitation(app, foreign_id) == "admin"


def test_unknown_invitation_is_404(client, seeder, utils):
    base = BASE_URL.format(_setup(seeder, utils))

    assert utils.put_json(f"{base}/4711", dict(roles=[])).status_code == 404
    assert utils.post_json(f"{base}/4711/delete", dict()).status_code == 404


# list


def test_list(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    seeder.create_invitation(admin_unit_id, "Zeta@test.de", ["admin", "event_verifier"])
    seeder.create_invitation(admin_unit_id, "alpha@test.de", [])

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert [(i["email"], i["roles"]) for i in body["items"]] == [
        ("alpha@test.de", []),
        ("Zeta@test.de", ["admin", "event_verifier"]),
    ]
    assert [c["name"] for c in body["role_choices"]] == ["admin", "event_verifier"]
    assert body["can_write"] is True


def test_list_out_of_range_is_404(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)

    assert utils.get_json(BASE_URL.format(admin_unit_id) + "?page=2").status_code == 404


# create


def test_get_create_form(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id) + "/create-form").json

    assert [c["title"] for c in body["role_choices"]] == [
        "Administrator:in",
        "Veranstaltungsexpert:in",
    ]
    assert body["list_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/organization_member_invitations"
    )


def test_create(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)

    response = utils.post_json(
        BASE_URL.format(admin_unit_id), dict(email="invited@test.de", roles=["admin"])
    )

    assert response.status_code == 201
    assert response.json["redirect_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/organization_member_invitations"
    )
    assert _invitation(app, response.json["id"]) == "admin"
    assert _flashes(client) == [
        ("success", "Mitgliedschaftseinladung erfolgreich erstellt")
    ]

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert [m["recipient"] for m in app.test_email_service.sent_emails] == [
        "invited@test.de"
    ]


def test_create_validates_the_email(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)

    response = utils.post_json(
        BASE_URL.format(admin_unit_id), dict(email="not-an-email", roles=[])
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["email"]


def test_create_unknown_role_is_a_field_error(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)

    response = utils.post_json(
        BASE_URL.format(admin_unit_id), dict(email="invited@test.de", roles=["boss"])
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["roles"]


# update


def test_update_roles(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de", [])

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{invitation_id}",
        dict(roles=["event_verifier"]),
    )

    assert response.status_code == 200
    assert response.json == dict(
        message="Mitgliedschaftseinladung erfolgreich aktualisiert"
    )
    assert _invitation(app, invitation_id) == "event_verifier"


def test_update_unknown_role_is_a_field_error(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de")

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{invitation_id}", dict(roles=["boss"])
    )

    assert response.status_code == 422
    assert _invitation(app, invitation_id) == "admin"


# delete


def test_delete(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de")

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{invitation_id}/delete", dict()
    )

    assert response.status_code == 200
    assert response.json == dict(
        message="Mitgliedschaftseinladung erfolgreich gelöscht"
    )
    assert _invitation(app, invitation_id) is None
