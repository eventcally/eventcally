from project.domain import commands, events
from project.models import AppInstallation


def test_install_app_command_creates_app_installation(app, db, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id)
    app_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id,
    )

    with app.app_context():
        message_bus = app.container.cqrs.message_bus()
        cmd = commands.InstallAppCommand.model_construct(
            admin_unit_id=admin_unit_id,
            app_id=app_id,
        )

        result = message_bus.handle_command(cmd)

        app_installation = db.session.get(AppInstallation, result.id)
        assert app_installation is not None
        assert app_installation.admin_unit_id == admin_unit_id
        assert app_installation.oauth2_client_id == app_id
        assert (
            app_installation.permissions
            == app_installation.oauth2_client.app_permissions
        )

        installation_events = [
            e
            for e in app.test_event_dispatcher.events
            if isinstance(e, events.AppInstallationCreated)
        ]
        assert len(installation_events) == 1

        event = installation_events[0]
        assert event.id == app_installation.id
        assert event.admin_unit_id == admin_unit_id
        assert event.app_id == app_id
        assert event.permissions == app_installation.permissions
