import pytest

from project.domain.events.organization_deletion_cancelled import (
    OrganizationDeletionCancelled,
)
from project.domain.events.organization_deletion_requested import (
    OrganizationDeletionRequested,
)
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def org():
    return OrganizationAggregate(id=10)


class TestOrganizationAggregateRequestDeletion:
    def test_sets_deletion_requested_at(self, org, actor):
        org.request_deletion(actor)
        assert org.deletion_requested_at is not None

    def test_sets_deletion_requested_by_id(self, org, actor):
        org.request_deletion(actor)
        assert org.deletion_requested_by_id == actor.user_id

    def test_appends_deletion_requested_event(self, org, actor):
        org.request_deletion(actor)
        assert len(org.domain_events) == 1
        event = org.domain_events[0]
        assert isinstance(event, OrganizationDeletionRequested)

    def test_event_has_correct_id(self, org, actor):
        org.request_deletion(actor)
        event = org.domain_events[0]
        assert event.id == org.id

    def test_event_has_correct_actor(self, org, actor):
        org.request_deletion(actor)
        event = org.domain_events[0]
        assert event.actor == actor


class TestOrganizationAggregateCancelDeletion:
    def test_clears_deletion_requested_at(self, org, actor):
        org.request_deletion(actor)
        org.cancel_deletion(actor)
        assert org.deletion_requested_at is None

    def test_clears_deletion_requested_by_id(self, org, actor):
        org.request_deletion(actor)
        org.cancel_deletion(actor)
        assert org.deletion_requested_by_id is None

    def test_appends_deletion_cancelled_event(self, org, actor):
        org.cancel_deletion(actor)
        assert len(org.domain_events) == 1
        event = org.domain_events[0]
        assert isinstance(event, OrganizationDeletionCancelled)

    def test_event_has_correct_id(self, org, actor):
        org.cancel_deletion(actor)
        event = org.domain_events[0]
        assert event.id == org.id


class TestOrganizationAggregateDefaults:
    def test_deletion_requested_at_defaults_none(self):
        org = OrganizationAggregate(id=1)
        assert org.deletion_requested_at is None

    def test_deletion_requested_by_id_defaults_none(self):
        org = OrganizationAggregate(id=1)
        assert org.deletion_requested_by_id is None


class TestOrganizationAggregateCreate:
    def test_creates_instance_with_required_fields(self, actor):
        org = OrganizationAggregate.create(
            actor=actor, name="My Crew", short_name="my_crew"
        )
        assert org.id == -1
        assert org.name == "My Crew"
        assert org.short_name == "my_crew"
        assert org.description is None
        assert org.url is None
        assert org.email is None
        assert org.phone is None
        assert org.fax is None
        assert org.location is None
        assert org.logo is None

    def test_creates_instance_with_all_fields(self, actor):
        from project.domain.models.entities.image_entity import ImageEntity
        from project.domain.models.value_objects.location_value_object import (
            LocationValueObject,
        )

        location = LocationValueObject(city="Goslar")
        logo = ImageEntity(id=-1, hash=-1, data=b"x", encoding_format="image/png")

        org = OrganizationAggregate.create(
            actor=actor,
            name="My Crew",
            short_name="my_crew",
            description="A crew",
            url="https://example.com",
            email="crew@example.com",
            phone="123",
            fax="456",
            location=location,
            logo=logo,
        )
        assert org.description == "A crew"
        assert org.url == "https://example.com"
        assert org.email == "crew@example.com"
        assert org.phone == "123"
        assert org.fax == "456"
        assert org.location == location
        assert org.logo == logo

    def test_create_raises_no_domain_event(self, actor):
        org = OrganizationAggregate.create(
            actor=actor, name="My Crew", short_name="my_crew"
        )
        assert org.domain_events == []


class TestOrganizationAggregateUpdate:
    def test_updates_settings_fields(self, org, actor):
        org.update(
            actor=actor,
            name="New Name",
            short_name="new_name",
            description="New description",
            url="https://example.com",
            email="new@example.com",
            phone="123",
            fax="456",
        )
        assert org.name == "New Name"
        assert org.short_name == "new_name"
        assert org.description == "New description"
        assert org.url == "https://example.com"
        assert org.email == "new@example.com"
        assert org.phone == "123"
        assert org.fax == "456"

    def test_updates_location_and_logo(self, org, actor):
        from project.domain.models.entities.image_entity import ImageEntity
        from project.domain.models.value_objects.location_value_object import (
            LocationValueObject,
        )

        location = LocationValueObject(city="Goslar")
        logo = ImageEntity(id=-1, hash=-1, data=b"x", encoding_format="image/png")

        org.update(actor=actor, location=location, logo=logo)

        assert org.location == location
        assert org.logo == logo

    def test_updates_verification_request_fields(self, org, actor):
        org.update(
            actor=actor,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_text="Please verify us",
            incoming_verification_requests_postal_codes=["12345"],
        )
        assert org.incoming_verification_requests_allowed is True
        assert org.incoming_verification_requests_text == "Please verify us"
        assert org.incoming_verification_requests_postal_codes == ["12345"]

    def test_leaves_verification_request_fields_untouched_when_omitted(
        self, org, actor
    ):
        org.update(
            actor=actor,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_text="Please verify us",
            incoming_verification_requests_postal_codes=["12345"],
        )
        org.update(actor=actor, name="New Name")

        assert org.incoming_verification_requests_allowed is True
        assert org.incoming_verification_requests_text == "Please verify us"
        assert org.incoming_verification_requests_postal_codes == ["12345"]

    def test_updates_widget_fields(self, org, actor):
        org.update(
            actor=actor,
            widget_font="Arial",
            widget_background_color="#000000",
            widget_primary_color="#111111",
            widget_link_color="#222222",
        )
        assert org.widget_font == "Arial"
        assert org.widget_background_color == "#000000"
        assert org.widget_primary_color == "#111111"
        assert org.widget_link_color == "#222222"

    def test_widget_fields_can_be_cleared(self, org, actor):
        org.update(actor=actor, widget_background_color="#000000")
        org.update(actor=actor, widget_background_color=None)
        assert org.widget_background_color is None

    def test_appends_organization_updated_event(self, org, actor):
        from project.domain.events.organization_updated import OrganizationUpdated

        org.update(actor=actor, name="New Name")

        event = org.get_first_domain_event_by_type(OrganizationUpdated)
        assert event is not None
        assert event.id == org.id
        assert event.actor == actor

    def test_update_with_no_changes_still_raises_event(self, org, actor):
        from project.domain.events.organization_updated import OrganizationUpdated

        org.update(actor=actor)

        assert org.get_first_domain_event_by_type(OrganizationUpdated) is not None

    def test_updates_admin_settings_fields(self, org, actor):
        org.update(
            actor=actor,
            incoming_reference_requests_allowed=True,
            can_create_other=True,
            can_invite_other=True,
            can_verify_other=True,
        )
        assert org.incoming_reference_requests_allowed is True
        assert org.can_create_other is True
        assert org.can_invite_other is True
        assert org.can_verify_other is True

    def test_leaves_admin_settings_fields_untouched_when_omitted(self, org, actor):
        org.update(
            actor=actor,
            incoming_reference_requests_allowed=True,
            can_create_other=True,
            can_invite_other=True,
            can_verify_other=True,
        )
        org.update(actor=actor, name="New Name")

        assert org.incoming_reference_requests_allowed is True
        assert org.can_create_other is True
        assert org.can_invite_other is True
        assert org.can_verify_other is True


class TestOrganizationAggregateDelete:
    def test_delete_does_not_raise(self, org, actor):
        org.delete(actor=actor)
