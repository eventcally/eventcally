def test_get_admin_units_with_due_delete_request(client, seeder, db, utils, app):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        import datetime

        from project.models import AdminUnit
        from project.services.admin_unit import get_admin_units_with_due_delete_request

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.deletion_requested_at = (
            datetime.datetime.utcnow() - datetime.timedelta(days=4)
        )
        db.session.commit()

        due_admin_units = get_admin_units_with_due_delete_request()
        assert len(due_admin_units) == 1
