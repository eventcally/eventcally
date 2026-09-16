import datetime

import pytest

from project.domain.errors import DuplicateError
from project.domain.events.event_place_created import EventPlaceCreated
from project.domain.events.event_place_updated import EventPlaceUpdated
from project.domain.events.member_invitation_created import MemberInvitationCreated
from project.domain.events.organization_invitation_created import (
    OrganizationInvitationCreated,
)
from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)
from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)
from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)
from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)
from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.infrastructure.read_repositories.sql_alchemy_event_read_repository import (
    SqlAlchemyEventReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_webhook_delivery_read_repository import (
    SqlAlchemyWebhookDeliveryReadRepository,
)
from project.infrastructure.repositories.sql_alchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from project.infrastructure.repositories.sql_alchemy_app_repository import (
    SqlAlchemyAppRepository,
)
from project.infrastructure.repositories.sql_alchemy_event_place_repository import (
    SqlAlchemyEventPlaceRepository,
)
from project.infrastructure.repositories.sql_alchemy_event_reference_repository import (
    SqlAlchemyEventReferenceRepository,
)
from project.infrastructure.repositories.sql_alchemy_member_invitation_repository import (
    SqlAlchemyMemberInvitationRepository,
)
from project.infrastructure.repositories.sql_alchemy_oauth2_client_repository import (
    SqlAlchemyOAuth2ClientRepository,
)
from project.infrastructure.repositories.sql_alchemy_oauth2_token_repository import (
    SqlAlchemyOAuth2TokenRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_app_installation_repository import (
    SqlAlchemyOrganizationAppInstallationRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_invitation_repository import (
    SqlAlchemyOrganizationInvitationRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_member_repository import (
    SqlAlchemyOrganizationMemberRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_relation_repository import (
    SqlAlchemyOrganizationRelationRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_repository import (
    SqlAlchemyOrganizationRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_verification_request_repository import (
    SqlAlchemyOrganizationVerificationRequestRepository,
)
from project.infrastructure.repositories.sql_alchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from project.infrastructure.repositories.sql_alchemy_webhook_delivery_attempt_repository import (
    SqlAlchemyWebhookDeliveryAttemptRepository,
)
from project.infrastructure.repositories.sql_alchemy_webhook_delivery_repository import (
    SqlAlchemyWebhookDeliveryRepository,
)
from project.infrastructure.repositories.sql_alchemy_webhook_repository import (
    SqlAlchemyWebhookEventRepository,
)
from project.models.admin_unit import AdminUnitRelation
from project.models.app import AppInstallation
from project.models.event_place import EventPlace
from project.models.event_reference import EventReference
from project.models.oauth import OAuth2Client
from project.models.webhook import Webhook
from project.models.webhook_delivery import WebhookDelivery
from project.models.webhook_event import WebhookEvent
from tests.seeder import Seeder


def _create_enabled_webhook_event_and_webhook(db):
    webhook_event = WebhookEvent(
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        event_type="event.created",
        payload={"id": 1},
    )
    webhook = Webhook(
        url="https://example.com/webhook",
        secret="secret-token",
        disabled=False,
        event_types=["event.created"],
    )
    db.session.add(webhook_event)
    db.session.add(webhook)
    db.session.commit()
    return webhook_event, webhook


def _create_event_place_photo():
    return ImageEntity.model_construct(
        id=-1,
        hash=123,
        data=b"event-place-photo",
        encoding_format="image/png",
        copyright_text="Copyright",
        license_id=None,
    )


def test_event_place_repository_add_get_roundtrip_with_photo(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        repo = SqlAlchemyEventPlaceRepository(db.session)
        place = EventPlaceAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            name="Photo Place",
            url="https://example.com/place",
            description="A place with a photo",
            location=LocationValueObject(city="Berlin", country="DE"),
            photo=_create_event_place_photo(),
        )

        repo.add(place)
        db.session.commit()

        loaded = repo.get(place.id)
        model = db.session.get(EventPlace, place.id)
        created_event = place.get_first_domain_event_by_type(EventPlaceCreated)

        assert isinstance(loaded, EventPlaceAggregate)
        assert loaded.id == place.id
        assert loaded.name == "Photo Place"
        assert loaded.url == "https://example.com/place"
        assert loaded.description == "A place with a photo"
        assert loaded.location.city == "Berlin"
        assert loaded.photo.id == model.photo.id
        assert loaded.photo.hash == model.photo.get_hash()
        assert place.photo.id == model.photo.id
        assert created_event.id == place.id
        assert created_event.photo.id == model.photo.id
        assert created_event.photo.hash == model.photo.get_hash()


def test_event_place_repository_update_and_remove(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        repo = SqlAlchemyEventPlaceRepository(db.session)
        place = EventPlaceAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            name="Original Place",
        )

        repo.add(place)
        db.session.commit()

        place.update(
            actor=Actor(user_id=1),
            name="Updated Place",
            url="https://example.com/updated-place",
            description="Updated description",
            location=LocationValueObject(city="Hamburg", country="DE"),
            photo=_create_event_place_photo(),
        )
        repo.update(place)
        db.session.commit()

        loaded = repo.get(place.id)
        model = db.session.get(EventPlace, place.id)
        updated_event = place.get_first_domain_event_by_type(EventPlaceUpdated)

        repo.remove(place)
        db.session.commit()

        assert isinstance(loaded, EventPlaceAggregate)
        assert loaded.id == place.id
        assert loaded.name == "Updated Place"
        assert loaded.url == "https://example.com/updated-place"
        assert loaded.description == "Updated description"
        assert loaded.location.city == "Hamburg"
        assert loaded.photo.id == model.photo.id
        assert loaded.photo.hash == model.photo.get_hash()
        assert place.photo.id == model.photo.id
        assert updated_event.photo.old is None
        assert updated_event.photo.new.id == model.photo.id
        assert updated_event.photo.new.hash == model.photo.get_hash()
        assert repo.get(place.id) is None


def test_event_read_repository_get_returns_event_read_model(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id=admin_unit_id, name="Infra Event")

    with app.app_context():
        repo = SqlAlchemyEventReadRepository(db.session)
        read_model = repo.get(event_id)

    assert read_model is not None
    assert read_model.id == event_id
    assert read_model.name == "Infra Event"
    assert read_model.admin_unit.id == admin_unit_id
    assert read_model.organizer.id is not None
    assert read_model.min_start_definition.start is not None
    assert user_id is not None


def test_event_read_repository_get_organizer_names(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Infra Organizer")

    with app.app_context():
        repo = SqlAlchemyEventReadRepository(db.session)

        assert repo.get_organizer_names(set()) == {}
        assert repo.get_organizer_names({organizer_id}) == {
            organizer_id: "Infra Organizer"
        }
        # Unknown ids are simply absent, which the summary reads as "deleted".
        assert repo.get_organizer_names({organizer_id, -1}) == {
            organizer_id: "Infra Organizer"
        }


def test_event_read_repository_get_place_names(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    place_id = seeder.upsert_event_place(admin_unit_id, "Infra Place")

    with app.app_context():
        repo = SqlAlchemyEventReadRepository(db.session)

        assert repo.get_place_names(set()) == {}
        assert repo.get_place_names({place_id}) == {place_id: "Infra Place"}
        assert repo.get_place_names({place_id, -1}) == {place_id: "Infra Place"}


def test_webhook_event_repository_roundtrip_and_delete_old_events(app, db):
    with app.app_context():
        repo = SqlAlchemyWebhookEventRepository(db.session)
        actor = Actor(user_id=1)

        old_event = WebhookEventAggregate.create(
            actor=actor,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=10),
            event_type="event.old",
            payload={"old": True},
        )
        recent_event = WebhookEventAggregate.create(
            actor=actor,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            event_type="event.recent",
            payload={"recent": True},
        )

        repo.add(old_event)
        repo.add(recent_event)
        db.session.commit()

        loaded = repo.get(recent_event.id)
        assert isinstance(loaded, WebhookEventAggregate)
        assert loaded.id == recent_event.id
        assert loaded.event_type == "event.recent"
        assert loaded.payload == {"recent": True}

        deleted_count = repo.delete_old_events(days=2)
        db.session.commit()

        assert deleted_count >= 1
        assert repo.get(old_event.id) is None
        assert repo.get(recent_event.id) is not None


def test_webhook_delivery_and_read_repository_roundtrip_aggregate(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        webhook_event, webhook = _create_enabled_webhook_event_and_webhook(db)

        app_model = OAuth2Client(
            admin_unit_id=admin_unit_id,
            app_permissions=["events:read"],
            webhook_id=webhook.id,
        )
        db.session.add(app_model)
        db.session.commit()

        actor = Actor(user_id=1)
        delivery_aggregate = WebhookDeliveryAggregate.create(
            actor=actor,
            webhook_event_id=webhook_event.id,
            app_id=app_model.id,
        )

        write_repo = SqlAlchemyWebhookDeliveryRepository(db.session)
        write_repo.add(delivery_aggregate)
        db.session.commit()

        loaded = write_repo.get(delivery_aggregate.id)
        assert isinstance(loaded, WebhookDeliveryAggregate)
        assert loaded.id == delivery_aggregate.id
        assert loaded.webhook_event_id == webhook_event.id

        read_repo = SqlAlchemyWebhookDeliveryReadRepository(db.session)
        read_model = read_repo.get(delivery_aggregate.id)

        assert read_model.id == delivery_aggregate.id
        assert read_model.webhook_event.event_type == "event.created"
        assert read_model.webhook.url == "https://example.com/webhook"
        assert read_model.webhook.secret == "secret-token"


def test_webhook_delivery_attempt_repository_roundtrip_aggregate(app, db):
    with app.app_context():
        webhook_event, webhook = _create_enabled_webhook_event_and_webhook(db)
        delivery = WebhookDelivery(
            webhook_event_id=webhook_event.id,
            webhook_id=webhook.id,
        )
        db.session.add(delivery)
        db.session.commit()

        actor = Actor(user_id=1)
        attempt = WebhookDeliveryAttemptAggregate.create(
            actor=actor,
            url="https://example.com/webhook",
            start_at=datetime.datetime.now(datetime.timezone.utc),
            end_at=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=1),
            webhook_delivery_id=delivery.id,
            status="ok",
            status_code="200",
        )

        repo = SqlAlchemyWebhookDeliveryAttemptRepository(db.session)
        repo.add(attempt)
        db.session.commit()

        loaded = repo.get(attempt.id)

        assert isinstance(loaded, WebhookDeliveryAttemptAggregate)
        assert loaded.id == attempt.id
        assert loaded.webhook_delivery_id == delivery.id
        assert loaded.status == "ok"
        assert loaded.status_code == "200"


def test_event_reference_repository_get_by_event_id_returns_aggregates(
    app, db, seeder: Seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="source@test.de", name="Source Unit"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="target@test.de", name="Target Unit"
    )
    event_id = seeder.create_event(admin_unit_id=source_admin_unit_id)

    with app.app_context():
        relation = AdminUnitRelation(
            source_admin_unit_id=target_admin_unit_id,
            target_admin_unit_id=source_admin_unit_id,
            verify=True,
            auto_verify_event_reference_requests=True,
        )
        reference = EventReference(
            admin_unit_id=target_admin_unit_id,
            event_id=event_id,
        )
        db.session.add(relation)
        db.session.add(reference)
        db.session.commit()

        repo = SqlAlchemyEventReferenceRepository(db.session)
        references = repo.get_by_event_id(event_id)

    assert len(references) == 1
    assert references[0].event_id == event_id
    assert references[0].admin_unit_id == target_admin_unit_id
    assert references[0] in repo.seen


def test_user_repository_get_and_get_all_with_ids_return_aggregates(app, db, seeder):
    user_a = seeder.create_user(email="repo-user-a@test.de")
    user_b = seeder.create_user(email="repo-user-b@test.de")

    with app.app_context():
        repo = SqlAlchemyUserRepository(db.session)
        loaded_user = repo.get(user_a)
        loaded_users = repo.get_all_with_ids([user_a, user_b])

    assert isinstance(loaded_user, UserAggregate)
    assert loaded_user.id == user_a
    assert {u.id for u in loaded_users} == {user_a, user_b}
    assert loaded_user in repo.seen
    assert loaded_user.is_platform_admin is False


def test_user_repository_marks_platform_admins(app, db, seeder):
    admin_user_id = seeder.create_user(email="repo-admin@test.de", admin=True)

    with app.app_context():
        repo = SqlAlchemyUserRepository(db.session)
        loaded_admin = repo.get(admin_user_id)

    assert loaded_admin.is_platform_admin is True


def test_api_key_repository_add_and_get_round_trip(app, db, seeder):
    user_id = seeder.create_user(email="api-key-owner@test.de")

    with app.app_context():
        repo = SqlAlchemyApiKeyRepository(db.session)
        api_key = ApiKeyAggregate.create(
            actor=Actor(user_id=user_id),
            name="My Key",
            key_hash="hash",
            user_id=user_id,
        )
        repo.add(api_key)
        db.session.commit()

        loaded = repo.get(api_key.id)
        loaded_name = loaded.name
        loaded_key_hash = loaded.key_hash
        loaded_user_id = loaded.user_id
        loaded_admin_unit_id = loaded.admin_unit_id

        loaded.name = "Renamed Key"
        repo.update(loaded)
        db.session.commit()

        renamed = repo.get(api_key.id)

        repo.remove(renamed)
        db.session.commit()

        removed = repo.get(api_key.id)

        not_found = repo.get(999999)

    assert isinstance(loaded, ApiKeyAggregate)
    assert loaded_name == "My Key"
    assert loaded_key_hash == "hash"
    assert loaded_user_id == user_id
    assert loaded_admin_unit_id is None
    assert renamed.name == "Renamed Key"
    assert removed is None
    assert not_found is None


def test_api_key_repository_count_for_owner(app, db, seeder):
    user_a = seeder.create_user(email="api-key-count-a@test.de")
    user_b = seeder.create_user(email="api-key-count-b@test.de")

    with app.app_context():
        repo = SqlAlchemyApiKeyRepository(db.session)

        assert repo.count_for_owner(user_a, None) == 0

        repo.add(
            ApiKeyAggregate.create(
                actor=Actor(user_id=user_a),
                name="Key 1",
                key_hash="hash-1",
                user_id=user_a,
            )
        )
        repo.add(
            ApiKeyAggregate.create(
                actor=Actor(user_id=user_a),
                name="Key 2",
                key_hash="hash-2",
                user_id=user_a,
            )
        )
        repo.add(
            ApiKeyAggregate.create(
                actor=Actor(user_id=user_b),
                name="Other Owner's Key",
                key_hash="hash-3",
                user_id=user_b,
            )
        )
        db.session.commit()

        count_a = repo.count_for_owner(user_a, None)
        count_b = repo.count_for_owner(user_b, None)

    assert count_a == 2
    assert count_b == 1


def test_oauth2_client_repository_add_get_update_remove_roundtrip(app, db, seeder):
    user_id = seeder.create_user(email="oauth2-client-owner@test.de")

    with app.app_context():
        repo = SqlAlchemyOAuth2ClientRepository(db.session)
        oauth2_client = OAuth2ClientAggregate.create(
            actor=Actor(user_id=user_id),
            name="My Client",
            client_id="client-id",
            client_secret="client-secret",
            redirect_uris=["https://example.com/callback"],
            scope="events:read",
            user_id=user_id,
        )
        repo.add(oauth2_client)
        db.session.commit()

        loaded = repo.get(oauth2_client.id)
        loaded_name = loaded.name
        loaded_client_id = loaded.client_id
        loaded_client_secret = loaded.client_secret
        loaded_redirect_uris = loaded.redirect_uris
        loaded_scope = loaded.scope
        loaded_user_id = loaded.user_id
        loaded_admin_unit_id = loaded.admin_unit_id

        loaded.name = "Renamed Client"
        repo.update(loaded)
        db.session.commit()

        renamed = repo.get(oauth2_client.id)

        repo.remove(renamed)
        db.session.commit()

        removed = repo.get(oauth2_client.id)

    assert isinstance(loaded, OAuth2ClientAggregate)
    assert loaded_name == "My Client"
    assert loaded_client_id == "client-id"
    assert loaded_client_secret == "client-secret"
    assert loaded_redirect_uris == ["https://example.com/callback"]
    assert loaded_scope == "events:read"
    assert loaded_user_id == user_id
    assert loaded_admin_unit_id is None
    assert renamed.name == "Renamed Client"
    assert removed is None


def test_oauth2_client_repository_excludes_app_rows(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    plain_client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)

    with app.app_context():
        repo = SqlAlchemyOAuth2ClientRepository(db.session)

        loaded_app_as_client = repo.get(app_id)
        loaded_plain_client = repo.get(plain_client_id)

    assert loaded_app_as_client is None
    assert loaded_plain_client is not None
    assert loaded_plain_client.id == plain_client_id


def test_app_repository_sets_client_credentials(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        repo = SqlAlchemyAppRepository(db.session)
        app_aggregate = AppAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            name="My App",
            app_permissions={"events:read"},
            client_id="app-client-id",
            client_secret="app-client-secret",
        )
        repo.add(app_aggregate)
        db.session.commit()

        loaded = repo.get(app_aggregate.id)

    assert loaded.client_id == "app-client-id"
    assert loaded.client_secret == "app-client-secret"


def test_oauth2_token_repository_get_and_update_roundtrip(app, db, seeder):
    user_id = seeder.create_user(email="oauth2-token-owner@test.de")

    with app.app_context():
        from project.models import OAuth2Token

        token = OAuth2Token()
        token.user_id = user_id
        token.access_token = "test-access-token"
        db.session.add(token)
        db.session.commit()
        token_id = token.id

    with app.app_context():
        repo = SqlAlchemyOAuth2TokenRepository(db.session)

        not_found = repo.get(999999)

        loaded = repo.get(token_id)
        loaded_user_id = loaded.user_id
        loaded_is_revoked = loaded.is_revoked

        loaded.is_revoked = True
        repo.update(loaded)
        db.session.commit()

        revoked = repo.get(token_id)

    assert not_found is None
    assert loaded_user_id == user_id
    assert loaded_is_revoked is False
    assert revoked.is_revoked is True


def test_organization_repository_updates_with_aggregate(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False, email="org-owner@test.de")

    with app.app_context():
        repo = SqlAlchemyOrganizationRepository(db.session)
        organization = repo.get(admin_unit_id)

        organization.request_deletion(actor=Actor(user_id=user_id))
        repo.update(organization)
        db.session.commit()

        loaded = repo.get(admin_unit_id)

    assert loaded.id == admin_unit_id
    assert loaded.deletion_requested_by_id == user_id
    assert loaded.deletion_requested_at is not None


def test_organization_app_installation_repository_aggregate_and_webhook_filter(
    app, db, seeder
):
    user_id, admin_unit_id = seeder.setup_base(log_in=False, email="app-owner@test.de")
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        app_model = db.session.get(OAuth2Client, app_id)
        app_model.webhook = Webhook(
            url="https://example.com/app-hook",
            secret="app-secret",
            disabled=False,
            event_types=["event.created"],
        )
        db.session.commit()

        repo = SqlAlchemyOrganizationAppInstallationRepository(db.session)
        installation = OrganisationAppInstallationAggregate.create(
            actor=Actor(user_id=user_id),
            admin_unit_id=admin_unit_id,
            app_id=app_id,
            permissions=list(app_model.app_permissions or []),
        )
        repo.add(installation)
        db.session.commit()

        loaded = repo.get(installation.id)
        filtered = repo.get_all_with_webhook(
            admin_unit_id=admin_unit_id,
            permissions=[],
            event_type="event.created",
        )
        app_model_app_permissions = app_model.app_permissions

    assert isinstance(loaded, OrganisationAppInstallationAggregate)
    assert loaded.id == installation.id
    assert loaded.app_id == app_id
    assert loaded.permissions == set(app_model_app_permissions or [])
    assert any(item.id == installation.id for item in filtered)


def test_webhook_delivery_read_repository_includes_app_installation_id(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False, email="read-owner@test.de")
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        app_model = db.session.get(OAuth2Client, app_id)
        app_model.webhook = Webhook(
            url="https://example.com/with-installation",
            secret="install-secret",
            disabled=False,
            event_types=["event.created"],
        )
        db.session.commit()

        installation = AppInstallation(
            admin_unit_id=admin_unit_id,
            oauth2_client_id=app_id,
            permissions=list(app_model.app_permissions or []),
        )
        webhook_event = WebhookEvent(
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            event_type="event.created",
            payload={"source": "integration-test"},
        )
        db.session.add(installation)
        db.session.add(webhook_event)
        db.session.flush()

        delivery = WebhookDelivery(
            webhook_event_id=webhook_event.id,
            webhook_id=app_model.webhook.id,
            app_installation_id=installation.id,
            app_id=app_id,
        )
        db.session.add(delivery)
        db.session.commit()

        read_repo = SqlAlchemyWebhookDeliveryReadRepository(db.session)
        read_model = read_repo.get(delivery.id)
        installation_id = installation.id

    assert read_model.id == delivery.id
    assert read_model.app_installation_id == installation_id
    assert read_model.webhook_event.payload["source"] == "integration-test"


def test_organization_relation_repository_add_get_update_remove_roundtrip(
    app, db, seeder: Seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="relation-source@test.de", name="Relation Source Unit"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="relation-target@test.de", name="Relation Target Unit"
    )

    with app.app_context():
        repo = SqlAlchemyOrganizationRelationRepository(db.session)
        relation = OrganizationRelationAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
            invited=True,
        )

        repo.add(relation)
        db.session.commit()

        loaded = repo.get(relation.id)

        assert isinstance(loaded, OrganizationRelationAggregate)
        assert loaded.id == relation.id
        assert loaded.source_admin_unit_id == source_admin_unit_id
        assert loaded.target_admin_unit_id == target_admin_unit_id
        assert loaded.invited is True
        assert loaded.verify is False
        assert loaded in repo.seen

        loaded.update(actor=Actor(user_id=1), verify=True)
        repo.update(loaded)
        db.session.commit()

        updated = repo.get(relation.id)
        assert updated.verify is True
        assert updated.invited is True

        repo.remove(updated)
        db.session.commit()

        assert repo.get(relation.id) is None


def test_organization_relation_repository_duplicate_raises_duplicate_error(
    app, db, seeder: Seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="dup-source@test.de", name="Dup Source Unit"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="dup-target@test.de", name="Dup Target Unit"
    )

    with app.app_context():
        repo = SqlAlchemyOrganizationRelationRepository(db.session)
        first = OrganizationRelationAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )
        repo.add(first)
        db.session.commit()

        second = OrganizationRelationAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )

        with pytest.raises(DuplicateError):
            repo.add(second)


def test_organization_relation_repository_get_by_source_and_target(
    app, db, seeder: Seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="gbst-source@test.de", name="GBST Source Unit"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="gbst-target@test.de", name="GBST Target Unit"
    )

    with app.app_context():
        repo = SqlAlchemyOrganizationRelationRepository(db.session)

        assert (
            repo.get_by_source_and_target(source_admin_unit_id, target_admin_unit_id)
            is None
        )

        relation = OrganizationRelationAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )
        repo.add(relation)
        db.session.commit()

        found = repo.get_by_source_and_target(
            source_admin_unit_id, target_admin_unit_id
        )
        assert found is not None
        assert found.id == relation.id
        assert found in repo.seen


def test_organization_verification_request_repository_add_get_update_remove_roundtrip(
    app, db, seeder: Seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="ovr-source@test.de", name="OVR Source Unit"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="ovr-target@test.de", name="OVR Target Unit"
    )

    with app.app_context():
        repo = SqlAlchemyOrganizationVerificationRequestRepository(db.session)
        verification_request = OrganizationVerificationRequestAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )

        repo.add(verification_request)
        db.session.commit()

        loaded = repo.get(verification_request.id)

        assert isinstance(loaded, OrganizationVerificationRequestAggregate)
        assert loaded.id == verification_request.id
        assert loaded.source_admin_unit_id == source_admin_unit_id
        assert loaded.target_admin_unit_id == target_admin_unit_id
        assert loaded.review_status == OrganizationVerificationRequestReviewStatus.inbox
        assert loaded in repo.seen

        loaded.approve(Actor(user_id=1))
        repo.update(loaded)
        db.session.commit()

        updated = repo.get(verification_request.id)
        assert updated.review_status == (
            OrganizationVerificationRequestReviewStatus.verified
        )

        repo.remove(updated)
        db.session.commit()

        assert repo.get(verification_request.id) is None


def test_organization_verification_request_repository_duplicate_raises_duplicate_error(
    app, db, seeder: Seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="ovr-dup-source@test.de", name="OVR Dup Source"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="ovr-dup-target@test.de", name="OVR Dup Target"
    )

    with app.app_context():
        repo = SqlAlchemyOrganizationVerificationRequestRepository(db.session)
        first = OrganizationVerificationRequestAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )
        repo.add(first)
        db.session.commit()

        second = OrganizationVerificationRequestAggregate.create(
            actor=Actor(user_id=1),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )

        with pytest.raises(DuplicateError):
            repo.add(second)


def test_organization_invitation_repository_add_get_update_remove_roundtrip(
    app, db, seeder: Seeder
):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        repo = SqlAlchemyOrganizationInvitationRepository(db.session)
        invitation = AdminUnitInvitationAggregate.create(
            actor=Actor(user_id=1),
            admin_unit_id=admin_unit_id,
            email="invitee@test.de",
            admin_unit_name="Future Org",
        )

        repo.add(invitation)
        db.session.commit()

        created_event = invitation.get_first_domain_event_by_type(
            OrganizationInvitationCreated
        )
        assert created_event.id == invitation.id

        loaded = repo.get(invitation.id)

        assert isinstance(loaded, AdminUnitInvitationAggregate)
        assert loaded.id == invitation.id
        assert loaded.admin_unit_id == admin_unit_id
        assert loaded.email == "invitee@test.de"
        assert loaded.admin_unit_name == "Future Org"
        assert loaded.relation_verify is False
        assert loaded in repo.seen

        loaded.update(actor=Actor(user_id=1), relation_verify=True)
        repo.update(loaded)
        db.session.commit()

        updated = repo.get(invitation.id)
        assert updated.relation_verify is True
        assert updated.admin_unit_name == "Future Org"

        repo.remove(updated)
        db.session.commit()

        assert repo.get(invitation.id) is None


def test_member_invitation_repository_add_get_update_remove_roundtrip(
    app, db, seeder: Seeder
):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        repo = SqlAlchemyMemberInvitationRepository(db.session)
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=Actor(user_id=1),
            admin_unit_id=admin_unit_id,
            email="invitee@test.de",
            roles=["admin"],
        )

        repo.add(invitation)
        db.session.commit()

        created_event = invitation.get_first_domain_event_by_type(
            MemberInvitationCreated
        )
        assert created_event.id == invitation.id

        loaded = repo.get(invitation.id)

        assert isinstance(loaded, AdminUnitMemberInvitationAggregate)
        assert loaded.id == invitation.id
        assert loaded.admin_unit_id == admin_unit_id
        assert loaded.email == "invitee@test.de"
        assert loaded.roles == ["admin"]
        assert loaded in repo.seen

        loaded.update(actor=Actor(user_id=1), roles=["event_verifier"])
        repo.update(loaded)
        db.session.commit()

        updated = repo.get(invitation.id)
        assert updated.roles == ["event_verifier"]

        repo.remove(updated)
        db.session.commit()

        assert repo.get(invitation.id) is None


def test_organization_member_repository_add_get_update_roundtrip_with_roles(
    app, db, seeder: Seeder
):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    # A fresh user with no existing AdminUnitMember row for this admin unit —
    # setup_base's own user is auto-added as an admin member by
    # insert_admin_unit_for_user, which would make get_by_admin_unit_and_user
    # non-None from the start.
    new_user_id = seeder.create_user(email="new-member@test.de")

    with app.app_context():
        repo = SqlAlchemyOrganizationMemberRepository(db.session)

        assert repo.get_by_admin_unit_and_user(admin_unit_id, new_user_id) is None

        member = OrganisationMemberAggregate.create(
            admin_unit_id=admin_unit_id, user_id=new_user_id, roles=["admin"]
        )
        repo.add(member)
        db.session.commit()

        loaded = repo.get_by_admin_unit_and_user(admin_unit_id, new_user_id)
        assert isinstance(loaded, OrganisationMemberAggregate)
        assert loaded.roles == ["admin"]
        assert loaded in repo.seen

        loaded.add_roles(["event_verifier", "not-a-real-role"])
        repo.update(loaded)
        db.session.commit()

        updated = repo.get_by_admin_unit_and_user(admin_unit_id, new_user_id)
        # "not-a-real-role" doesn't resolve to an AdminUnitMemberRole row and
        # is silently dropped, mirroring add_roles_to_admin_unit_member.
        assert updated.roles == ["admin", "event_verifier"]

        loaded_by_id = repo.get(updated.id)
        assert isinstance(loaded_by_id, OrganisationMemberAggregate)
        assert loaded_by_id.id == updated.id
        assert loaded_by_id.roles == ["admin", "event_verifier"]

        repo.remove(loaded_by_id)
        db.session.commit()

        assert repo.get(updated.id) is None
        assert repo.get_by_admin_unit_and_user(admin_unit_id, new_user_id) is None
