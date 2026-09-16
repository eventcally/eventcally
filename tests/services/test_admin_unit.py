def test_get_admin_units_with_due_delete_request(client, seeder, db, utils, app):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        import datetime

        from project.models import AdminUnit
        from project.services.admin_unit import get_admin_units_with_due_delete_request

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.deletion_requested_at = datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(days=4)
        db.session.commit()

        due_admin_units = get_admin_units_with_due_delete_request()
        assert len(due_admin_units) == 1


def test_add_roles_to_admin_unit_member_skips_unknown_role(client, seeder, db, app):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")

    with app.app_context():
        from project.models import AdminUnit, User
        from project.services.admin_unit import (
            add_roles_to_admin_unit_member,
            add_user_to_admin_unit,
        )

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        user = db.session.get(User, other_user_id)
        member = add_user_to_admin_unit(user, admin_unit)
        db.session.commit()

        add_roles_to_admin_unit_member(member, ["admin", "not-a-real-role"])
        db.session.commit()

        assert [role.name for role in member.roles] == ["admin"]
