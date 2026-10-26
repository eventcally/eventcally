"""Parity of the modular update/delete pages for organizers, places and organization
invitations: what the forms are prefilled with (the organizer and place forms are Vue
shells; their prefill is tested in the BFF tests), the delete titles, and the 404/401
paths. Written against the ORM object loading, so it must pass unchanged once the
objects come from the query bus."""

import pytest


def _input_value(soup, name):
    field = soup.find(["input", "textarea", "select"], attrs={"name": name})
    assert field is not None, name

    if field.name == "textarea":
        return field.text.strip()

    return field.get("value")


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _organizer_url(utils, endpoint, admin_unit_id, organizer_id):
    return utils.get_url(
        f"manage_admin_unit.event_organizer_{endpoint}",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )


def _place_url(utils, endpoint, admin_unit_id, place_id):
    return utils.get_url(
        f"manage_admin_unit.event_place_{endpoint}",
        id=admin_unit_id,
        event_place_id=place_id,
    )


def _invitation_url(utils, endpoint, admin_unit_id, invitation_id):
    return utils.get_url(
        f"manage_admin_unit.organization_invitation_{endpoint}",
        id=admin_unit_id,
        organization_invitation_id=invitation_id,
    )


def test_organizer_delete_shows_name(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mein Organisator")

    response = utils.get_ok(
        _organizer_url(utils, "delete", admin_unit_id, organizer_id)
    )

    assert "Möchtest du 'Mein Organisator' löschen?" in _text(utils, response)


def test_place_delete_shows_name(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    response = utils.get_ok(_place_url(utils, "delete", admin_unit_id, place_id))

    assert "Möchtest du 'Mein Ort' löschen?" in _text(utils, response)


def test_invitation_update_prefills_fields(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id,
        email="invited@test.de",
        admin_unit_name="Eingeladene Crew",
        relation_auto_verify_event_reference_requests=True,
        relation_verify=False,
    )

    response = utils.get_ok(
        _invitation_url(utils, "update", admin_unit_id, invitation_id)
    )
    soup = utils.get_soup(response)

    assert _input_value(soup, "admin_unit_name") == "Eingeladene Crew"
    assert soup.find(
        attrs={"name": "relation_auto_verify_event_reference_requests"}
    ).has_attr("checked")
    relation_verify = soup.find(attrs={"name": "relation_verify"})
    assert relation_verify is None or not relation_verify.has_attr("checked")
    utils.assert_response_contains(response, "invited@test.de")


def test_invitation_delete_shows_display_name_and_id(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.get_ok(
        _invitation_url(utils, "delete", admin_unit_id, invitation_id)
    )

    assert f"Möchtest du 'Organisationseinladung {invitation_id}' löschen?" in _text(
        utils, response
    )


@pytest.mark.parametrize("endpoint", ["update", "delete"])
@pytest.mark.parametrize("url_factory", [_organizer_url, _place_url, _invitation_url])
def test_unknown_object_is_not_found(seeder, utils, url_factory, endpoint):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get(url_factory(utils, endpoint, admin_unit_id, 4711))

    utils.assert_response_notFound(response)


@pytest.mark.parametrize("endpoint", ["update", "delete"])
def test_organizer_of_other_organization_is_unauthorized(seeder, utils, endpoint):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mein Organisator")
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        _organizer_url(utils, endpoint, other_admin_unit_id, organizer_id)
    )


@pytest.mark.parametrize("endpoint", ["update", "delete"])
def test_invitation_of_other_organization_is_unauthorized(seeder, utils, endpoint):
    user_id, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        _invitation_url(utils, endpoint, other_admin_unit_id, invitation_id)
    )
