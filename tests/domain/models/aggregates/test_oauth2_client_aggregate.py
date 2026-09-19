import pytest

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestOAuth2ClientAggregateCreate:
    def test_creates_instance_with_user_owner(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="My Client",
            client_id="client-id",
            client_secret="client-secret",
            user_id=1,
        )
        assert oauth2_client.id == -1
        assert oauth2_client.name == "My Client"
        assert oauth2_client.client_id == "client-id"
        assert oauth2_client.client_secret == "client-secret"
        assert oauth2_client.user_id == 1
        assert oauth2_client.admin_unit_id is None

    def test_creates_instance_with_admin_unit_owner(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="Org Client",
            client_id="client-id",
            client_secret="client-secret",
            admin_unit_id=2,
        )
        assert oauth2_client.user_id is None
        assert oauth2_client.admin_unit_id == 2

    def test_both_owners_set_raises_constraint_error(self, actor):
        with pytest.raises(ConstraintError):
            OAuth2ClientAggregate.create(
                actor=actor,
                name="Client",
                client_id="client-id",
                client_secret="client-secret",
                user_id=1,
                admin_unit_id=2,
            )

    def test_no_owner_set_raises_constraint_error(self, actor):
        with pytest.raises(ConstraintError):
            OAuth2ClientAggregate.create(
                actor=actor,
                name="Client",
                client_id="client-id",
                client_secret="client-secret",
            )

    def test_optional_fields_default(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="Client",
            client_id="client-id",
            client_secret="client-secret",
            user_id=1,
        )
        assert oauth2_client.redirect_uris == []
        assert oauth2_client.scope is None


class TestOAuth2ClientAggregateUpdate:
    def test_update_changes_name(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="Old Name",
            client_id="client-id",
            client_secret="client-secret",
            user_id=1,
        )
        oauth2_client.update(actor=actor, name="New Name")
        assert oauth2_client.name == "New Name"

    def test_update_changes_redirect_uris_and_scope(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="Client",
            client_id="client-id",
            client_secret="client-secret",
            user_id=1,
        )
        oauth2_client.update(
            actor=actor,
            redirect_uris=["https://example.com/callback"],
            scope="events:read",
        )
        assert oauth2_client.redirect_uris == ["https://example.com/callback"]
        assert oauth2_client.scope == "events:read"

    def test_update_with_no_changes_leaves_fields_untouched(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="Name",
            client_id="client-id",
            client_secret="client-secret",
            user_id=1,
        )
        oauth2_client.update(actor=actor)
        assert oauth2_client.name == "Name"
        assert oauth2_client.redirect_uris == []
        assert oauth2_client.scope is None


class TestOAuth2ClientAggregateDelete:
    def test_delete_does_not_raise(self, actor):
        oauth2_client = OAuth2ClientAggregate.create(
            actor=actor,
            name="Name",
            client_id="client-id",
            client_secret="client-secret",
            user_id=1,
        )
        oauth2_client.delete(actor=actor)
