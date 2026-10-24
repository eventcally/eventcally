import pytest


def _shell(utils, admin_unit_id, event_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(
        f"/manage/admin_unit/{admin_unit_id}/outgoing_event_reference_request"
        f"/create_for_event/{event_id}"
    )


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _urls(admin_unit_id, event_id):
    base = f"/bff/manage/organizations/{admin_unit_id}/events/{event_id}"
    return dict(
        form=f"{base}/reference-request-form",
        lookup=f"{base}/reference-request-organizations",
        base=f"{base}/reference-requests",
    )


def _reference_request(app, event_id, admin_unit_id):
    with app.app_context():
        from project.infrastructure.models import EventReferenceRequest

        request = EventReferenceRequest.query.filter(
            EventReferenceRequest.event_id == event_id,
            EventReferenceRequest.admin_unit_id == admin_unit_id,
        ).first()
        return request and (request.id, request.review_status.name)


@pytest.fixture
def setup(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Other Crew", verified=True
    )
    _shell(utils, admin_unit_id, event_id)
    return admin_unit_id, event_id, other_id


# access


def test_anonymous_is_401(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    urls = _urls(admin_unit_id, event_id)

    assert utils.get_json(urls["form"]).status_code == 401
    assert utils.get_json(urls["lookup"]).status_code == 401
    assert utils.post_json(urls["base"], dict(admin_unit_id=1)).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew", verified=True)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")
    urls = _urls(admin_unit_id, event_id)

    assert utils.get_json(urls["form"]).status_code == 403
    assert utils.get_json(urls["lookup"]).status_code == 403
    assert utils.post_json(urls["base"], dict(admin_unit_id=1)).status_code == 403


def test_unverified_organization_is_403(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_admin_unit(seeder.create_user("other@test.de"), "Other Crew")
    urls = _urls(admin_unit_id, event_id)

    assert utils.get_json(urls["form"]).status_code == 403
    assert utils.get_json(urls["lookup"]).status_code == 403


def test_unknown_event_is_404(client, utils, setup):
    admin_unit_id, _, _ = setup
    urls = _urls(admin_unit_id, 4711)

    assert utils.get_json(urls["form"]).status_code == 404
    assert utils.get_json(urls["lookup"]).status_code == 404
    assert utils.post_json(urls["base"], dict(admin_unit_id=1)).status_code == 404


def test_event_of_another_organization_is_404(client, seeder, utils, setup):
    admin_unit_id, _, other_id = setup
    other_event_id = seeder.create_event(other_id)
    urls = _urls(admin_unit_id, other_event_id)

    assert utils.get_json(urls["form"]).status_code == 404
    assert (
        utils.post_json(urls["base"], dict(admin_unit_id=other_id)).status_code == 404
    )


def test_write_requires_csrf(client, seeder):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    response = client.post(
        _urls(admin_unit_id, event_id)["base"], json=dict(admin_unit_id=1)
    )

    assert response.status_code == 400


# form and lookup


def test_get_form(client, utils, setup):
    admin_unit_id, event_id, _ = setup

    body = utils.get_json_ok(_urls(admin_unit_id, event_id)["form"]).json

    assert body["event"]["id"] == event_id
    assert body["event"]["name"]
    assert body["list_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/outgoing_event_reference_requests"
    )


def test_lookup_excludes_own_and_not_accepting_organizations(
    client, app, db, seeder, utils, setup
):
    admin_unit_id, event_id, other_id = setup
    closed_id = seeder.create_admin_unit(
        seeder.create_user("closed@test.de"), "Other Closed", verified=True
    )
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, closed_id).incoming_reference_requests_allowed = False
        db.session.commit()

    items = utils.get_json_ok(
        _urls(admin_unit_id, event_id)["lookup"] + "?keyword=C"
    ).json["items"]
    assert items == [dict(id=other_id, name="Other Crew")]

    names = {
        item["name"]
        for item in utils.get_json_ok(_urls(admin_unit_id, event_id)["lookup"]).json[
            "items"
        ]
    }
    assert names == {"Other Crew"}


def test_lookup_includes_unverified_with_permission(
    client, app, db, seeder, utils, setup
):
    admin_unit_id, event_id, other_id = setup
    unverified_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Other Unverified"
    )
    urls = _urls(admin_unit_id, event_id)

    names = lambda: {  # noqa: E731
        item["id"]
        for item in utils.get_json_ok(urls["lookup"] + "?keyword=Other").json["items"]
    }
    assert names() == {other_id}

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = True
        db.session.commit()

    assert names() == {other_id, unverified_id}


# create


def test_create(client, app, utils, setup):
    admin_unit_id, event_id, other_id = setup

    response = utils.post_json(
        _urls(admin_unit_id, event_id)["base"], dict(admin_unit_id=other_id)
    )

    assert response.status_code == 201
    request_id, status = _reference_request(app, event_id, other_id)
    assert status == "inbox"
    assert response.json == dict(
        id=request_id,
        verified=False,
        redirect_url=f"/manage/admin_unit/{admin_unit_id}/outgoing_event_reference_requests",
    )
    assert _flashes(client) == [
        (
            "success",
            "Empfehlungsanfrage an Other Crew erfolgreich erstellt. Du wirst "
            "benachrichtigt, nachdem die andere Organisation die Veranstaltung "
            "geprüft hat.",
        )
    ]

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "other@test.de"


def test_create_auto_verify(client, app, seeder, utils, setup):
    admin_unit_id, event_id, other_id = setup
    seeder.create_admin_unit_relation(other_id, admin_unit_id, True)

    response = utils.post_json(
        _urls(admin_unit_id, event_id)["base"], dict(admin_unit_id=other_id)
    )

    assert response.status_code == 201
    assert response.json["verified"] is True
    assert _reference_request(app, event_id, other_id)[1] == "verified"
    assert _flashes(client) == [
        ("success", "Other Crew hat deine Empfehlungsanfrage akzeptiert")
    ]


def test_create_requires_organization(client, utils, setup):
    admin_unit_id, event_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id, event_id)["base"], dict())

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["admin_unit_id"]
    assert response.json["errors"][0]["msg"] == "Dieses Feld ist erforderlich."


def test_create_unknown_organization_is_404(client, utils, setup):
    admin_unit_id, event_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, event_id)["base"], dict(admin_unit_id=4711)
    )

    assert response.status_code == 404


def test_create_duplicate_is_a_400(client, app, utils, setup):
    admin_unit_id, event_id, other_id = setup
    url = _urls(admin_unit_id, event_id)["base"]

    assert utils.post_json(url, dict(admin_unit_id=other_id)).status_code == 201
    response = utils.post_json(url, dict(admin_unit_id=other_id))

    assert response.status_code == 400
    assert response.json["name"] == "DuplicateError"
    # Translated like the flash of the old form.
    assert response.json["message"].startswith("Ein Eintrag")
