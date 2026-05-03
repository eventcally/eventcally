from project.domain import commands, events
from project.models import AppInstallation


def test_uninstall_app_command_removes_app_installation(app, db, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id)
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    app_installation_id = seeder.install_app(app_id, admin_unit_id)

    with app.app_context():
        message_bus = app.container.cqrs.message_bus()
        cmd = commands.UninstallAppCommand.model_construct(
            id=app_installation_id,
        )

        message_bus.handle_command(cmd)

        db.session.expire_all()
        app_installation = db.session.get(AppInstallation, app_installation_id)
        assert app_installation is None

        matching_events = [
            e
            for e in app.test_event_dispatcher.events
            if isinstance(e, events.AppUninstalled)
        ]
        assert len(matching_events) == 1

        event = matching_events[0]
        assert event.id == app_installation_id
        assert event.admin_unit_id == admin_unit_id
        assert event.app_id == app_id
