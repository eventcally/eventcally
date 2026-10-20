"""Guards the wiring done by `create_app`: blueprints, API, Flask-Admin and CLI groups."""

REPRESENTATIVE_ENDPOINTS = {
    "main.contact",
    "main.authorize",
    "admin.admin",
    "admin_next.shell",
    "bff.bff_admin.users",
    "manage.organization_create",
    "manage_admin_unit.api_key",
    "user.api_key",
    "security.login",
    "api_v1_event",
    "api_v1_event_category_list",
    "api_v1_dump",
    "flask_admin.static",
    "static",
}


def test_url_map_keeps_registered_endpoints(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert len(list(app.url_map.iter_rules())) >= 629
    assert REPRESENTATIVE_ENDPOINTS <= endpoints


def test_cli_groups_are_registered(app):
    commands = set(app.cli.list_commands(None))

    assert {"cache", "data", "dump", "event", "seo", "user", "test"} <= commands
