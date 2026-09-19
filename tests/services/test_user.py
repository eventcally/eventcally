from tests.seeder import Seeder


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


def test_get_ghost_users(client, seeder: Seeder, db, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_user("second@test.de", confirm=False)

    with app.app_context():
        from project.services.user import get_ghost_users

        ghost_users = get_ghost_users()
        assert len(ghost_users) == 0
