import pytest

SETTINGS_URL = "/bff/manage/organizations/{}/settings"
AVAILABILITY_URL = "/bff/manage/organizations/{}/settings/name-availability"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/update")


def _body(**values):
    body = dict(
        name="Meine neue Crew",
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


def _admin_unit(app, admin_unit_id):
    with app.app_context():
        from project.infrastructure.seed_helpers import get_admin_unit_by_id

        unit = get_admin_unit_by_id(admin_unit_id)
        return dict(
            name=unit.name,
            short_name=unit.short_name,
            description=unit.description,
            city=unit.location.city,
            postal_code=unit.location.postalCode,
            street=unit.location.street,
            url=unit.url,
            email=unit.email,
            phone=unit.phone,
            fax=unit.fax,
            logo=unit.logo and (unit.logo.data, unit.logo.copyright_text),
            verification=(
                unit.incoming_verification_requests_allowed,
                unit.incoming_verification_requests_text,
                unit.incoming_verification_requests_postal_codes,
            ),
        )


def _logo(seeder, **values):
    logo = dict(
        image_base64=seeder.get_default_image_upload_base64(),
        copyright_text="Me",
        license_id=None,
    )
    logo.update(values)
    return logo


def _foreign_admin_unit(seeder):
    owner_id = seeder.create_user(email="other@test.de")
    return seeder.create_admin_unit(owner_id, name="Andere Crew")


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)

    for call in (
        lambda: utils.get_json(SETTINGS_URL.format(admin_unit_id)),
        lambda: utils.put_json(SETTINGS_URL.format(admin_unit_id), _body()),
        lambda: utils.get_json(AVAILABILITY_URL.format(admin_unit_id) + "?name=x"),
    ):
        assert call().status_code == 401


def test_member_without_settings_write_is_403(client, seeder, utils):
    _, admin_unit_id, _ = seeder.setup_base_event_verifier()
    # The member may open the event list: that page carries the CSRF token.
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/events")

    assert utils.get_json(SETTINGS_URL.format(admin_unit_id)).status_code == 403
    assert (
        utils.put_json(SETTINGS_URL.format(admin_unit_id), _body()).status_code == 403
    )
    assert (
        utils.get_json(AVAILABILITY_URL.format(admin_unit_id) + "?name=x").status_code
        == 403
    )


def test_foreign_organization_is_403(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    other_id = _foreign_admin_unit(seeder)

    assert utils.get_json(SETTINGS_URL.format(other_id)).status_code == 403
    assert utils.put_json(SETTINGS_URL.format(other_id), _body()).status_code == 403
    assert _admin_unit(app, other_id)["name"] == "Andere Crew"


def test_unknown_organization_is_403(client, seeder, utils):
    seeder.setup_base()

    assert utils.get_json(SETTINGS_URL.format(4711)).status_code == 403


def test_put_requires_csrf(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    assert (
        utils.put_json(SETTINGS_URL.format(admin_unit_id), _body()).status_code == 400
    )


# get


def test_get(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    body = utils.get_json_ok(SETTINGS_URL.format(admin_unit_id)).json

    assert body["id"] == admin_unit_id
    assert body["name"] == "Meine Crew"
    assert body["short_name"] == "meinecrew"
    assert body["location"]["postalCode"] == "12345"
    assert body["location"]["city"] == "City"
    assert body["logo"] is None
    assert body["can_verify_other"] is False
    assert body["verification_requests"] is None
    assert body["deletion_requested_at"] is None
    assert isinstance(body["licenses"], list)


def test_get_with_logo_and_verification_requests(client, seeder, utils):
    user_id = seeder.create_user()
    utils.login()
    admin_unit_id = seeder.create_admin_unit(
        user_id,
        can_verify_other=True,
        incoming_verification_requests_allowed=True,
    )
    _shell(utils, admin_unit_id)
    uri = seeder.get_default_image_upload_base64()
    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(logo=_logo(seeder), verification_requests=dict(allowed=True, text="Hi")),
    )
    assert response.status_code == 204

    body = utils.get_json_ok(SETTINGS_URL.format(admin_unit_id)).json

    assert body["logo"]["image_base64"].startswith("data:image/png;base64,")
    assert body["logo"]["copyright_text"] == "Me"
    assert body["can_verify_other"] is True
    assert body["verification_requests"] == dict(
        allowed=True, text="Hi", postal_codes=[]
    )
    assert uri


def test_get_licenses(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import License

        db.session.add(License(code="CC0", name="Creative Commons Zero"))
        db.session.commit()

    body = utils.get_json_ok(SETTINGS_URL.format(admin_unit_id)).json

    assert "CC0 (Creative Commons Zero)" in [item["name"] for item in body["licenses"]]


# put


def test_put(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(url="", email="", phone=None, fax="  "),
    )

    assert response.status_code == 204
    unit = _admin_unit(app, admin_unit_id)
    assert unit["name"] == "Meine neue Crew"
    assert unit["short_name"] == "neuecrew"
    assert unit["description"] == "Beschreibung"
    assert (unit["city"], unit["postal_code"], unit["street"]) == (
        "Goslar",
        "38640",
        "Markt 1",
    )
    assert (unit["url"], unit["email"], unit["phone"], unit["fax"]) == (
        None,
        None,
        None,
        None,
    )


def test_put_contact_data(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    utils.put_json(SETTINGS_URL.format(admin_unit_id), _body())

    unit = _admin_unit(app, admin_unit_id)
    assert (unit["url"], unit["email"], unit["phone"], unit["fax"]) == (
        "https://example.org",
        "info@example.org",
        "0123",
        "0124",
    )


def test_put_keeps_own_name(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(name="Meine Crew", short_name="meinecrew"),
    )

    assert response.status_code == 204


def test_put_name_and_short_name_taken(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    owner_id = seeder.create_user(email="other@test.de")
    seeder.create_admin_unit(owner_id, name="Andere Crew")

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(name="Andere Crew", short_name="anderecrew"),
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
def test_put_invalid_is_422(client, seeder, utils, values, loc):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(SETTINGS_URL.format(admin_unit_id), _body(**values))

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == loc


def test_put_logo_new_unchanged_and_removed(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    url = SETTINGS_URL.format(admin_unit_id)

    assert utils.put_json(url, _body(logo=_logo(seeder))).status_code == 204
    stored = _admin_unit(app, admin_unit_id)["logo"]
    assert stored[0] and stored[1] == "Me"

    response = utils.put_json(
        url, _body(logo=_logo(seeder, image_base64=None, copyright_text="Other"))
    )
    assert response.status_code == 204
    assert _admin_unit(app, admin_unit_id)["logo"] == (stored[0], "Other")

    assert utils.put_json(url, _body(logo=None)).status_code == 204
    assert _admin_unit(app, admin_unit_id)["logo"] is None


def test_put_logo_unchanged_without_stored_logo_removes_nothing(
    client, app, seeder, utils
):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(logo=_logo(seeder, image_base64=None)),
    )

    assert response.status_code == 204
    assert _admin_unit(app, admin_unit_id)["logo"] is None


def test_put_logo_too_small(client, seeder, utils):
    import base64
    import io

    from PIL import Image

    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    buffer = io.BytesIO()
    Image.new("RGB", (50, 50)).save(buffer, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id), _body(logo=_logo(seeder, image_base64=uri))
    )

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["logo", "image_base64"]


def test_put_logo_without_copyright_and_taken_name(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    owner_id = seeder.create_user(email="other@test.de")
    seeder.create_admin_unit(owner_id, name="Andere Crew")

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(name="Andere Crew", logo=_logo(seeder, copyright_text=" ")),
    )

    utils.assert_response_unprocessable_entity(response)
    assert [e["loc"] for e in response.json["errors"]] == [
        ["name"],
        ["logo", "copyright_text"],
    ]


def test_put_verification_requests(client, app, seeder, utils):
    user_id = seeder.create_user()
    utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, can_verify_other=True)
    _shell(utils, admin_unit_id)

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(
            verification_requests=dict(
                allowed=True, text="Please verify us", postal_codes=[" 12345", "54321"]
            )
        ),
    )

    assert response.status_code == 204
    assert _admin_unit(app, admin_unit_id)["verification"] == (
        True,
        "Please verify us",
        ["12345", "54321"],
    )


def test_put_verification_requests_ignored_without_can_verify_other(
    client, app, db, seeder, utils
):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        unit = db.session.get(AdminUnit, admin_unit_id)
        unit.incoming_verification_requests_postal_codes = ["12345"]
        db.session.commit()

    response = utils.put_json(
        SETTINGS_URL.format(admin_unit_id),
        _body(
            verification_requests=dict(allowed=True, text="x", postal_codes=["99999"])
        ),
    )

    assert response.status_code == 204
    assert _admin_unit(app, admin_unit_id)["verification"] == (False, None, ["12345"])


def test_put_base_error_is_400(client, seeder, utils, mocker):
    from project.domain.errors import BaseError

    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    mocker.patch(
        "project.application.message_bus.MessageBus.handle_command",
        side_effect=BaseError("Nope"),
    )

    response = utils.put_json(SETTINGS_URL.format(admin_unit_id), _body())

    assert response.status_code == 400


# name availability


def test_name_availability(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    owner_id = seeder.create_user(email="other@test.de")
    seeder.create_admin_unit(owner_id, name="Andere Crew")
    url = AVAILABILITY_URL.format(admin_unit_id)

    taken = utils.get_json_ok(f"{url}?name=Andere Crew&short_name=anderecrew").json
    free = utils.get_json_ok(f"{url}?name=Frei&short_name=frei").json
    own = utils.get_json_ok(f"{url}?name=Meine Crew&short_name=meinecrew").json
    none_given = utils.get_json_ok(url).json

    assert taken == dict(name_taken=True, short_name_taken=True)
    assert free == dict(name_taken=False, short_name_taken=False)
    assert own == dict(name_taken=False, short_name_taken=False)
    assert none_given == dict(name_taken=None, short_name_taken=None)


def test_name_availability_name_only(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    body = utils.get_json_ok(AVAILABILITY_URL.format(admin_unit_id) + "?name=Frei").json

    assert body == dict(name_taken=False, short_name_taken=None)
