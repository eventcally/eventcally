def test_to_aggregate(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        from project.models import OAuth2Client, Webhook

        client = OAuth2Client(
            id=1,
            admin_unit_id=admin_unit_id,
            description="A client",
            app_permissions=["perm1", "perm2"],
            homepage_url="https://example.com",
            setup_url="https://example.com/setup",
            webhook=Webhook(
                url="https://example.com/webhook",
                secret="secret-token",
                disabled=False,
                event_types=["event.created"],
            ),
        )
        metadata = client.client_metadata or {}
        metadata["client_name"] = "Test Client"
        client.set_client_metadata(metadata)

        aggregate = OAuth2Client.to_aggregate(client)
        assert aggregate.id == client.id
        assert aggregate.admin_unit_id == client.admin_unit_id
