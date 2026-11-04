"""The 404/401 paths of the organizer and place update shells (the forms are Vue pages,
their prefill is tested in the BFF tests)."""

import pytest


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


@pytest.mark.parametrize(
    "endpoint, url_factory",
    [
        ("update", _organizer_url),
        ("update", _place_url),
    ],
)
def test_unknown_object_is_not_found(seeder, utils, url_factory, endpoint):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get(url_factory(utils, endpoint, admin_unit_id, 4711))

    utils.assert_response_notFound(response)


def test_organizer_of_other_organization_is_unauthorized(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mein Organisator")
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        _organizer_url(utils, "update", other_admin_unit_id, organizer_id)
    )
