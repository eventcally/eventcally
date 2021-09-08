def test_update_event_dates_with_recurrence_rule(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base(admin=False, log_in=False)
    seeder.create_event(admin_unit_id)
    admin_id = seeder.create_user(email="admin@test.de", admin=True)
    seeder.create_user(email="normal@test.de", admin=False)

    with app.app_context():
        from project.services.user import find_all_users_with_role

        admins = find_all_users_with_role("admin")
        assert len(admins) == 1

        admin = admins[0]
        assert admin.id == admin_id
        assert admin.email == "admin@test.de"
