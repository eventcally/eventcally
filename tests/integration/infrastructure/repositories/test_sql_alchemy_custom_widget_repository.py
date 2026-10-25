from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)
from project.domain.models.entities.actor import Actor
from project.infrastructure.repositories.sql_alchemy_custom_widget_repository import (
    SqlAlchemyCustomWidgetRepository,
)


def test_add_get_update_remove(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    actor = Actor(user_id=user_id)
    with app.app_context():
        repo = SqlAlchemyCustomWidgetRepository(db.session)
        widget = CustomWidgetAggregate.create(
            actor=actor,
            admin_unit_id=admin_unit_id,
            widget_type="search",
            name="Widget",
            settings={"color": "red"},
        )

        repo.add(widget)
        db.session.commit()

        loaded = repo.get(widget.id)
        assert loaded.id == widget.id
        assert loaded.admin_unit_id == admin_unit_id
        assert loaded.widget_type == "search"
        assert loaded.name == "Widget"
        assert loaded.settings == {"color": "red"}

        widget.update(actor=actor, name="Renamed", settings={"color": "blue"})
        repo.update(widget)
        db.session.commit()

        loaded = repo.get(widget.id)
        assert loaded.name == "Renamed"
        assert loaded.settings == {"color": "blue"}

        repo.remove(widget)
        db.session.commit()
        assert repo.get(widget.id) is None


def test_get_unknown_returns_none(app, db):
    with app.app_context():
        assert SqlAlchemyCustomWidgetRepository(db.session).get(-1) is None
