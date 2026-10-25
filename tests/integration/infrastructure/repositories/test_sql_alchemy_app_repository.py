from project.domain.events.app_created import AppCreated
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.infrastructure.repositories.sql_alchemy_app_repository import (
    SqlAlchemyAppRepository,
)


def test_add_get_update_remove(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyAppRepository(db.session)
        app_aggregate = AppAggregate.create(
            actor=actor,
            admin_unit_id=admin_unit_id,
            name="Repo App",
            app_permissions={"events:read"},
            client_id="repo-client-id",
            client_secret="repo-client-secret",
            webhook=WebhookValueObject(
                url="https://example.com/hook",
                secret="secret",
                disabled=False,
                event_types=["event.created"],
            ),
        )

        repo.add(app_aggregate)
        db.session.commit()

        created = app_aggregate.get_first_domain_event_by_type(AppCreated)
        assert created.id == app_aggregate.id

        loaded = repo.get(app_aggregate.id)
        assert loaded.name == "Repo App"
        assert loaded.app_permissions == {"events:read"}
        assert loaded.webhook.url == "https://example.com/hook"

        app_aggregate.update(actor=actor, name="Renamed App")
        repo.update(app_aggregate)
        db.session.commit()
        assert repo.get(app_aggregate.id).name == "Renamed App"

        repo.remove(app_aggregate)
        db.session.commit()
        assert repo.get(app_aggregate.id) is None
