import datetime

from project.domain.events.event_place_created import EventPlaceCreated
from project.domain.events.event_place_updated import EventPlaceUpdated
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
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
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.infrastructure.read_repositories.sql_alchemy_event_read_repository import (
    SqlAlchemyEventReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_webhook_delivery_read_repository import (
    SqlAlchemyWebhookDeliveryReadRepository,
)
from project.infrastructure.repositories.sql_alchemy_event_place_repository import (
    SqlAlchemyEventPlaceRepository,
)
from project.infrastructure.repositories.sql_alchemy_event_reference_repository import (
    SqlAlchemyEventReferenceRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_app_installation_repository import (
    SqlAlchemyOrganizationAppInstallationRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_repository import (
    SqlAlchemyOrganizationRepository,
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


def test_webhook_delivery_and_read_repository_roundtrip_aggregate(app, db):
    with app.app_context():
        webhook_event, webhook = _create_enabled_webhook_event_and_webhook(db)

        actor = Actor(user_id=1)
        delivery_aggregate = WebhookDeliveryAggregate.create(
            actor=actor,
            webhook_event_id=webhook_event.id,
            webhook_id=webhook.id,
        )

        write_repo = SqlAlchemyWebhookDeliveryRepository(db.session)
        write_repo.add(delivery_aggregate)
        db.session.commit()

        loaded = write_repo.get(delivery_aggregate.id)
        assert isinstance(loaded, WebhookDeliveryAggregate)
        assert loaded.id == delivery_aggregate.id
        assert loaded.webhook_event_id == webhook_event.id
        assert loaded.webhook_id == webhook.id

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
    assert loaded.permissions == list(app_model_app_permissions or [])
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
