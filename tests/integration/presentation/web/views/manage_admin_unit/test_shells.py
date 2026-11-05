"""The query-backed object loading of the manage shells.

Uses the organizer update shell as the vehicle: the query handler factory is
overridden with a fake, so the pages render whatever read model the fake returns.
"""

from typing import Optional

import pytest
from dependency_injector import providers

from project.application.queries import (
    GetCurrentOrganizationQuery,
    GetManageableOrganizationQuery,
    GetManageMenuOptionsQuery,
    GetSiteNoticesQuery,
    ListManageableOrganizationsQuery,
)
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerEditReadModel,
)

ACCESS_QUERIES = (
    GetManageableOrganizationQuery,
    GetCurrentOrganizationQuery,
    GetManageMenuOptionsQuery,
    GetSiteNoticesQuery,
    ListManageableOrganizationsQuery,
)


class _FakeHandler:
    def __init__(self, result: Optional[EventOrganizerEditReadModel]):
        self.result = result
        self.queries = []

    def handle(self, query):
        self.queries.append(query)
        return self.result


@pytest.fixture
def fake_object(app):
    def install(result):
        fake = _FakeHandler(result)
        real = app.container.cqrs.query_handler_factory()
        app.container.cqrs.query_handler_factory.override(
            providers.Object(
                lambda query_type: (
                    real(query_type) if query_type in ACCESS_QUERIES else fake
                )
            )
        )
        return fake

    yield install

    app.container.cqrs.query_handler_factory.reset_override()


def _url(utils, endpoint, admin_unit_id, organizer_id=4711):
    return utils.get_url(
        f"manage_admin_unit.event_organizer_{endpoint}",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )


def test_update_renders_read_model_from_query_bus(seeder, utils, fake_object):
    _, admin_unit_id = seeder.setup_base()
    fake = fake_object(
        EventOrganizerEditReadModel(
            id=4711, admin_unit_id=admin_unit_id, name="Organizer from the bus"
        )
    )

    response = utils.get_ok(_url(utils, "update", admin_unit_id))

    assert b'<div id="app"' in response.data
    assert [query.id for query in fake.queries] == [4711]


def test_missing_object_is_not_found(seeder, utils, fake_object):
    _, admin_unit_id = seeder.setup_base()
    fake_object(None)

    utils.assert_response_notFound(utils.get(_url(utils, "update", admin_unit_id)))


def test_object_of_other_organization_is_unauthorized(seeder, utils, fake_object):
    _, admin_unit_id = seeder.setup_base()
    fake_object(
        EventOrganizerEditReadModel(id=4711, admin_unit_id=admin_unit_id + 1, name="X")
    )

    utils.get_unauthorized(_url(utils, "update", admin_unit_id))


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
