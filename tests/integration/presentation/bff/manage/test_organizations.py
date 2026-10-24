import pytest

AVAILABILITY_URL = "/bff/manage/organizations/name-availability"
FORM_URL = "/bff/manage/organizations/create-form"
CREATE_URL = "/bff/manage/organizations"


def _shell(utils, invitation_id=None):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    url = "/manage/organization/create"

    if invitation_id:
        url += f"?invitation_id={invitation_id}"

    utils.get_ok(url)


def _body(**values):
    body = dict(
        name="Neue Crew",
        short_name="neuecrew",
        description="Beschreibung",
        location=dict(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            state="Niedersachsen",
            latitude=51.9,
            longitude=10.4,
        ),
        logo=None,
        url="https://example.org",
        email="info@example.org",
        phone="0123",
        fax="0124",
    )
    body.update(values)
    return body


def _logo(seeder, **values):
    logo = dict(
        image_base64=seeder.get_default_image_upload_base64(),
        copyright_text="Me",
        license_id=None,
    )
    logo.update(values)
    return logo


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _organization(app, name):
    with app.app_context():
        from project.infrastructure.seed_helpers import (
            get_admin_unit_by_name,
            get_event_organizer,
            get_event_place,
        )

        unit = get_admin_unit_by_name(name)

        if unit is None:
            return None

        organizer = get_event_organizer(unit.id, name)
        place = get_event_place(unit.id, unit.location.city)
        return dict(
            id=unit.id,
            short_name=unit.short_name,
            description=unit.description,
            city=unit.location.city,
            postal_code=unit.location.postalCode,
            url=unit.url,
            email=unit.email,
            phone=unit.phone,
            fax=unit.fax,
            logo=unit.logo and unit.logo.copyright_text,
            organizer_city=organizer.location.city,
            organizer_email=organizer.email,
            place_postal_code=place.location.postalCode,
            roles={role.name for role in unit.members[0].roles},
            member_user_id=unit.members[0].user_id,
            relations=[
                (
                    relation.source_admin_unit_id,
                    relation.verify,
                    relation.auto_verify_event_reference_requests,
                    relation.invited,
                )
                for relation in unit.incoming_relations
            ],
        )


def _invitation(seeder, **values):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(
        user_id, can_invite_other=True, can_verify_other=True
    )
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id, **values)
    seeder.create_user("invited@test.de")
    return admin_unit_id, invitation_id


# access


def test_anonymous_is_401(client, seeder, utils):
    for call in (
        lambda: utils.get_json(AVAILABILITY_URL + "?name=x"),
        lambda: utils.get_json(FORM_URL),
        lambda: utils.post_json(CREATE_URL, _body()),
    ):
        assert call().status_code == 401


def test_post_requires_csrf(client, seeder, utils):
    seeder.create_user()
    utils.login()

    assert utils.post_json(CREATE_URL, _body()).status_code == 400


def test_name_availability_is_not_an_organization_id(client, seeder, utils):
    seeder.create_user()
    utils.login()

    assert utils.get_json(AVAILABILITY_URL + "?name=x").status_code == 200


# name availability


def test_name_availability(client, seeder, utils):
    owner_id = seeder.create_user(email="other@test.de")
    seeder.create_admin_unit(owner_id, name="Andere Crew")
    seeder.create_user()
    utils.login()

    taken = utils.get_json_ok(
        f"{AVAILABILITY_URL}?name=Andere Crew&short_name=anderecrew"
    )
    free = utils.get_json_ok(f"{AVAILABILITY_URL}?name=Frei&short_name=frei")
    none_given = utils.get_json_ok(AVAILABILITY_URL)
    name_only = utils.get_json_ok(f"{AVAILABILITY_URL}?name=Frei")

    assert taken.json == dict(name_taken=True, short_name_taken=True)
    assert free.json == dict(name_taken=False, short_name_taken=False)
    assert none_given.json == dict(name_taken=None, short_name_taken=None)
    assert name_only.json == dict(name_taken=False, short_name_taken=None)


def test_name_availability_exclude_own_organization(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    own = utils.get_json_ok(
        f"{AVAILABILITY_URL}?name=Meine Crew&short_name=meinecrew&exclude_id={admin_unit_id}"
    )
    taken = utils.get_json_ok(
        f"{AVAILABILITY_URL}?name=Meine Crew&short_name=meinecrew"
    )

    assert own.json == dict(name_taken=False, short_name_taken=False)
    assert taken.json == dict(name_taken=True, short_name_taken=True)


def test_name_availability_exclude_foreign_organization_is_403(client, seeder, utils):
    seeder.setup_base()
    owner_id = seeder.create_user(email="other@test.de")
    other_id = seeder.create_admin_unit(owner_id, name="Andere Crew")

    response = utils.get_json(f"{AVAILABILITY_URL}?name=x&exclude_id={other_id}")

    assert response.status_code == 403


# create form


def test_form_plain_user(client, seeder, utils):
    seeder.create_user()
    utils.login()

    body = utils.get_json_ok(FORM_URL).json

    assert body["name"] == ""
    assert body["invitation_id"] is None
    assert body["relation"] is None
    assert body["licenses"]


def test_form_closed_phase_is_403(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.create_user()
    utils.login()

    assert utils.get_json(FORM_URL).status_code == 403


def test_form_closed_phase_platform_admin(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.create_user(admin=True)
    utils.login()

    assert utils.get_json(FORM_URL).status_code == 200


def test_form_closed_phase_member_with_can_create_other(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    user_id = seeder.create_user(admin=False)
    utils.login()
    seeder.create_admin_unit(user_id, can_create_other=True)

    assert utils.get_json(FORM_URL).status_code == 200


def test_form_deletion_requested_is_403(client, app, db, seeder, utils):
    import datetime

    user_id = seeder.create_user()
    utils.login()

    with app.app_context():
        from project.infrastructure.models import User

        db.session.get(User, user_id).deletion_requested_at = datetime.datetime.now(
            datetime.UTC
        )
        db.session.commit()

    assert utils.get_json(FORM_URL).status_code == 403


def test_form_invitation(client, seeder, utils):
    _, invitation_id = _invitation(seeder)
    utils.login("invited@test.de")

    body = utils.get_json_ok(f"{FORM_URL}?invitation_id={invitation_id}").json

    assert body["name"] == "Invited Organization"
    assert body["invitation_id"] == invitation_id
    assert body["relation"] is None


def test_form_invitation_ignores_closed_phase(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    _, invitation_id = _invitation(seeder)
    utils.login("invited@test.de")

    assert (
        utils.get_json(f"{FORM_URL}?invitation_id={invitation_id}").status_code == 200
    )


def test_form_foreign_invitation_is_403(client, seeder, utils):
    _, invitation_id = _invitation(seeder)
    seeder.create_user("other@test.de")
    utils.login("other@test.de")

    assert (
        utils.get_json(f"{FORM_URL}?invitation_id={invitation_id}").status_code == 403
    )


def test_form_unknown_invitation_is_404(client, seeder, utils):
    seeder.create_user()
    utils.login()

    assert utils.get_json(f"{FORM_URL}?invitation_id=4711").status_code == 404


@pytest.mark.parametrize(
    "flags, expected",
    [
        (
            dict(can_verify_other=True, incoming_reference_requests_allowed=False),
            (True, False),
        ),
        (
            dict(can_verify_other=False, incoming_reference_requests_allowed=True),
            (False, True),
        ),
        (
            dict(can_verify_other=True, incoming_reference_requests_allowed=True),
            (True, True),
        ),
        (dict(can_verify_other=False, incoming_reference_requests_allowed=False), None),
    ],
)
def test_form_relation_options(client, seeder, utils, flags, expected):
    user_id = seeder.create_user(admin=False)
    utils.login()
    seeder.create_admin_unit(user_id, **flags)

    relation = utils.get_json_ok(FORM_URL).json["relation"]

    if expected is None:
        assert relation is None
    else:
        assert relation == dict(
            organization_name="Meine Crew",
            can_verify=expected[0],
            can_auto_verify=expected[1],
        )


def test_form_no_relation_without_relation_permission(client, seeder, utils):
    seeder.setup_base_event_verifier()

    assert utils.get_json_ok(FORM_URL).json["relation"] is None


# create


def test_post(client, app, seeder, utils):
    user_id = seeder.create_user()
    utils.login()
    _shell(utils)

    response = utils.post_json(
        CREATE_URL, _body(logo=_logo(seeder, copyright_text="EventCally"))
    )

    assert response.status_code == 201
    organization = _organization(app, "Neue Crew")
    assert response.json == dict(
        id=organization["id"],
        verified=False,
        redirect_url=(
            f"/manage/admin_unit/{organization['id']}/outgoing_organization_verification_requests"
        ),
    )
    assert organization["short_name"] == "neuecrew"
    assert organization["description"] == "Beschreibung"
    assert organization["city"] == "Goslar"
    assert organization["postal_code"] == "38640"
    assert organization["url"] == "https://example.org"
    assert organization["email"] == "info@example.org"
    assert organization["phone"] == "0123"
    assert organization["fax"] == "0124"
    assert organization["logo"] == "EventCally"
    assert organization["organizer_city"] == "Goslar"
    assert organization["organizer_email"] == "info@example.org"
    assert organization["place_postal_code"] == "38640"
    assert organization["roles"] >= {"admin", "event_verifier"}
    assert organization["member_user_id"] == user_id
    assert organization["relations"] == []
    assert _flashes(client) == [
        (
            "warning",
            "Die Organisation ist nicht verifiziert. Veranstaltungen sind daher nicht öffentlich sichtbar.",
        ),
        ("success", "Organisation erfolgreich erstellt"),
    ]


def test_post_minimal_without_stored_logo(client, app, seeder, utils):
    seeder.create_user()
    utils.login()
    _shell(utils)

    response = utils.post_json(
        CREATE_URL,
        _body(
            logo=dict(image_base64=None, copyright_text="Me"),
            description=None,
            url="",
            email=" ",
            phone=None,
            fax=None,
        ),
    )

    assert response.status_code == 201
    organization = _organization(app, "Neue Crew")
    assert organization["logo"] is None
    assert organization["url"] is None


def test_post_name_and_short_name_taken(client, seeder, utils):
    seeder.create_user()
    utils.login()
    owner_id = seeder.create_user(email="other@test.de")
    seeder.create_admin_unit(owner_id, name="Andere Crew")
    _shell(utils)

    response = utils.post_json(
        CREATE_URL, _body(name="Andere Crew", short_name="anderecrew")
    )

    utils.assert_response_unprocessable_entity(response)
    assert [(e["loc"], e["msg"]) for e in response.json["errors"]] == [
        (["name"], "Der Name ist bereits vergeben"),
        (["short_name"], "Der Kurzname ist bereits vergeben"),
    ]


@pytest.mark.parametrize(
    "values, loc",
    [
        (dict(short_name="bad name!"), ["short_name"]),
        (dict(short_name="abc"), ["short_name"]),
        (dict(name="abc"), ["name"]),
        (dict(location=dict(postalCode="38640", city="")), ["location", "city"]),
        (dict(location=dict(postalCode="", city="Goslar")), ["location", "postalCode"]),
        (dict(url="x" * 256), ["url"]),
    ],
)
def test_post_invalid_is_422(client, seeder, utils, values, loc):
    seeder.create_user()
    utils.login()
    _shell(utils)

    response = utils.post_json(CREATE_URL, _body(**values))

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == loc


def test_post_logo_too_small(client, seeder, utils):
    import base64
    import io

    from PIL import Image

    seeder.create_user()
    utils.login()
    _shell(utils)
    buffer = io.BytesIO()
    Image.new("RGB", (50, 50)).save(buffer, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

    response = utils.post_json(CREATE_URL, _body(logo=_logo(seeder, image_base64=uri)))

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["logo", "image_base64"]


def test_post_logo_without_copyright(client, seeder, utils):
    seeder.create_user()
    utils.login()
    _shell(utils)

    response = utils.post_json(
        CREATE_URL, _body(logo=_logo(seeder, copyright_text=" "))
    )

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["logo", "copyright_text"]


def test_post_closed_phase_is_403(client, app, seeder, utils):
    seeder.create_user()
    utils.login()
    _shell(utils)
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True

    assert utils.post_json(CREATE_URL, _body()).status_code == 403
    assert _organization(app, "Neue Crew") is None


def test_post_base_error_is_400(client, seeder, utils, mocker):
    from project.domain.errors import BaseError

    seeder.create_user()
    utils.login()
    _shell(utils)
    mocker.patch(
        "project.application.message_bus.MessageBus.handle_command",
        side_effect=BaseError("Nope"),
    )

    assert utils.post_json(CREATE_URL, _body()).status_code == 400


def test_post_from_invitation(client, app, db, seeder, utils):
    admin_unit_id, invitation_id = _invitation(
        seeder, relation_auto_verify_event_reference_requests=True, relation_verify=True
    )
    utils.login("invited@test.de")
    _shell(utils, invitation_id)

    response = utils.post_json(
        CREATE_URL,
        _body(name="Invited Organization", short_name="invitedorganization")
        | dict(invitation_id=invitation_id),
    )

    assert response.status_code == 201
    organization = _organization(app, "Invited Organization")
    assert response.json["verified"] is True
    assert response.json["redirect_url"] == f"/manage/admin_unit/{organization['id']}"
    assert organization["relations"] == [(admin_unit_id, True, True, True)]

    with app.app_context():
        from project.infrastructure.models import AdminUnitInvitation

        assert db.session.get(AdminUnitInvitation, invitation_id) is None
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "test@test.de"
    assert _flashes(client) == [("success", "Organisation erfolgreich erstellt")]


def test_post_foreign_invitation_is_403(client, app, seeder, utils):
    _, invitation_id = _invitation(seeder)
    seeder.create_user("other@test.de")
    utils.login("other@test.de")
    _shell(utils)

    response = utils.post_json(CREATE_URL, _body() | dict(invitation_id=invitation_id))

    assert response.status_code == 403
    assert _organization(app, "Neue Crew") is None


def test_post_with_relation(client, app, seeder, utils):
    user_id = seeder.create_user(admin=False)
    utils.login()
    admin_unit_id = seeder.create_admin_unit(
        user_id, can_verify_other=True, incoming_reference_requests_allowed=False
    )
    _shell(utils)

    response = utils.post_json(
        CREATE_URL,
        _body(name="Other Crew", short_name="othercrew")
        | dict(
            relation_verify=True, relation_auto_verify_event_reference_requests=True
        ),
    )

    assert response.status_code == 201
    organization = _organization(app, "Other Crew")
    # auto verify is not offered without incoming_reference_requests_allowed
    assert organization["relations"] == [(admin_unit_id, True, False, False)]
    assert response.json["verified"] is True
    assert response.json["redirect_url"] == f"/manage/admin_unit/{organization['id']}"


def test_post_with_relation_auto_verify(client, app, seeder, utils):
    user_id = seeder.create_user(admin=False)
    utils.login()
    admin_unit_id = seeder.create_admin_unit(
        user_id, can_verify_other=False, incoming_reference_requests_allowed=True
    )
    _shell(utils)

    response = utils.post_json(
        CREATE_URL,
        _body(name="Other Crew", short_name="othercrew")
        | dict(
            relation_verify=True, relation_auto_verify_event_reference_requests=True
        ),
    )

    assert response.status_code == 201
    organization = _organization(app, "Other Crew")
    # verify is not offered without can_verify_other
    assert organization["relations"] == [(admin_unit_id, False, True, False)]


def test_post_closed_phase_member_with_can_create_other(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    user_id = seeder.create_user(admin=False)
    utils.login()
    seeder.create_admin_unit(user_id, can_create_other=True)
    _shell(utils)

    response = utils.post_json(CREATE_URL, _body(name="Other Crew", short_name="other"))

    assert response.status_code == 201
