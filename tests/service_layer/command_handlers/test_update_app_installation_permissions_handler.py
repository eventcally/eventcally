from project.domain import commands, events
from project.models import AppInstallation


def test_update_app_installation_permissions_command_sets_current_app_permissions(
    app,
    db,
    seeder,
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id)
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    app_installation_id = seeder.install_app(app_id, admin_unit_id)

    with app.app_context():
        app_installation = db.session.get(AppInstallation, app_installation_id)
        new_permissions = app_installation.oauth2_client.app_permissions
        app_installation.permissions = []
        db.session.commit()

        message_bus = app.container.cqrs.message_bus()
        cmd = commands.UpdateAppInstallationPermissionsCommand.model_construct(
            id=app_installation_id,
            permissions=new_permissions,
        )

        message_bus.handle_command(cmd)

        db.session.expire_all()
        app_installation = db.session.get(AppInstallation, app_installation_id)
        assert app_installation.permissions == new_permissions

        matching_events = [
            e
            for e in app.test_event_dispatcher.events
            if isinstance(e, events.AppInstallationPermissionsUpdated)
        ]
        assert len(matching_events) == 1

        event = matching_events[0]
        assert event.id == app_installation_id
        assert event.admin_unit_id == admin_unit_id
        assert event.app_id == app_id
        assert event.permissions == new_permissions
