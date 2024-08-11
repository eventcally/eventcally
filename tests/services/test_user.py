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


def test_add_favorite_event(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.services.user import add_favorite_event, get_favorite_event

        assert add_favorite_event(user_id, event_id)
        assert add_favorite_event(user_id, event_id) is False

        favorite = get_favorite_event(user_id, event_id)
        assert favorite is not None


def test_remove_favorite_event(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    seeder.add_favorite_event(user_id, event_id)

    with app.app_context():
        from project.services.user import has_favorite_event, remove_favorite_event

        assert remove_favorite_event(user_id, event_id)
        assert remove_favorite_event(user_id, event_id) is False
        assert has_favorite_event(user_id, event_id) is False


def test_get_users_with_due_delete_request(client, seeder, db, utils, app):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        import datetime

        from project.models import User
        from project.services.user import get_users_with_due_delete_request

        user = db.session.get(User, user_id)
        user.deletion_requested_at = datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(days=4)
        db.session.commit()

        due_users = get_users_with_due_delete_request()
        assert len(due_users) == 1
