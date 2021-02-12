def test_has_admin_unit_member_role(client, app, db, seeder):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()

    with app.app_context():
        from project.access import has_admin_unit_member_role
        from project.models import AdminUnitMember

        member = AdminUnitMember.query.get(member_id)
        assert has_admin_unit_member_role(member, "admin") is False


def test_has_current_user_member_role_for_admin_unit(client, app, db, seeder):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()

    with app.test_request_context():
        with app.app_context():
            from flask_login import login_user

            from project.access import has_current_user_member_role_for_admin_unit
            from project.models import AdminUnitMember

            member = AdminUnitMember.query.get(member_id)
            login_user(member.user)

            assert (
                has_current_user_member_role_for_admin_unit(admin_unit_id, "admin")
                is False
            )
