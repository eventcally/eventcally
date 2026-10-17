"""The opt-in query-backed object loading of the modular update/delete views, and
view handlers without an ORM `model`.

Uses the organizer manage handler as the vehicle: the query handler factory is
overridden with a fake, so the pages render whatever read model the fake returns.
"""

from typing import Optional

import pytest
from dependency_injector import providers

from project.application.queries import (
    GetCurrentMemberGrantsQuery,
    GetCurrentOrganizationQuery,
    GetManageableOrganizationQuery,
    GetManageMenuOptionsQuery,
    GetSiteNoticesQuery,
    ListManageableOrganizationsQuery,
)
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerEditReadModel,
)
from project.views.manage_admin_unit.event_organizer.view_handler import (
    ViewHandler,
    handler,
)

ACCESS_QUERIES = (
    GetManageableOrganizationQuery,
    GetCurrentOrganizationQuery,
    GetManageMenuOptionsQuery,
    GetCurrentMemberGrantsQuery,
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

    soup = utils.get_soup(response)
    assert soup.find("input", attrs={"name": "name"})["value"] == (
        "Organizer from the bus"
    )
    assert [query.id for query in fake.queries] == [4711]


@pytest.mark.parametrize("endpoint", ["update", "delete"])
def test_missing_object_is_not_found(seeder, utils, fake_object, endpoint):
    _, admin_unit_id = seeder.setup_base()
    fake_object(None)

    utils.assert_response_notFound(utils.get(_url(utils, endpoint, admin_unit_id)))


@pytest.mark.parametrize("endpoint", ["update", "delete"])
def test_object_of_other_organization_is_unauthorized(
    seeder, utils, fake_object, endpoint
):
    _, admin_unit_id = seeder.setup_base()
    fake_object(
        EventOrganizerEditReadModel(id=4711, admin_unit_id=admin_unit_id + 1, name="X")
    )

    utils.get_unauthorized(_url(utils, endpoint, admin_unit_id))


def test_delete_instruction_uses_object_title(seeder, utils, fake_object, mocker):
    _, admin_unit_id = seeder.setup_base()
    fake_object(
        EventOrganizerEditReadModel(id=4711, admin_unit_id=admin_unit_id, name="X")
    )
    mocker.patch.object(ViewHandler, "get_object_title", return_value="Title marker")

    response = utils.get_ok(_url(utils, "delete", admin_unit_id))

    utils.assert_response_contains(response, "Title marker")


def test_handler_without_model_keeps_names_and_permissions(app):
    assert handler.get_permission_entity() == "event_organizers"
    assert handler.get_id_query_arg_name() == "event_organizer_id"
    assert handler.permissions == {"event_organizers:read", "event_organizers:write"}
    assert handler.endpoints == {
        "create": "event_organizer_create",
        "update": "event_organizer_update",
        "delete": "event_organizer_delete",
        "list": "event_organizers",
    }

    with app.test_request_context(headers={"Accept-Language": "de"}):
        assert handler.get_model_display_name() == "Veranstalter"
        assert handler.get_model_display_name_plural() == "Veranstalter"


def test_display_audit_of_read_models(app):
    from datetime import datetime

    from project.application.read_models.audit_read_model import AuditReadModel
    from project.views.modular.base_display import BaseDisplay

    class Display(BaseDisplay):
        pass

    display = Display()
    read_model = EventOrganizerEditReadModel(id=1, admin_unit_id=1, name="X")
    audited = read_model.model_copy(
        update={"audit": AuditReadModel(created_at=datetime(2026, 1, 1))}
    )

    assert not display.should_show_audit(read_model)
    assert display.should_show_audit(audited)
