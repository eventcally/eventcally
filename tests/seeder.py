class Seeder(object):
    def __init__(self, app, db):
        self._app = app
        self._db = db

    def create_user(
        self, email="test@test.de", password="MeinPasswortIstDasBeste", admin=False
    ):
        from project.services.user import upsert_user, add_admin_roles_to_user

        with self._app.app_context():
            user = upsert_user(email, password)

            if admin:
                add_admin_roles_to_user(email)

            self._db.session.commit()
            user_id = user.id

        return user_id

    def create_admin_unit(self, user_id, name):
        from project.models import AdminUnit
        from project.services.user import get_user
        from project.services.admin_unit import insert_admin_unit_for_user

        with self._app.app_context():
            user = get_user(user_id)
            admin_unit = AdminUnit()
            admin_unit.name = name
            insert_admin_unit_for_user(admin_unit, user)
            self._db.session.commit()
            admin_unit_id = admin_unit.id

        return admin_unit_id

    def create_admin_unit_member(self, admin_unit_id, role_names):
        from project.services.user import get_user
        from project.services.admin_unit import (
            get_admin_unit_by_id,
            add_user_to_admin_unit_with_roles,
        )

        with self._app.app_context():
            user_id = self.create_user()
            user = get_user(user_id)
            admin_unit = get_admin_unit_by_id(admin_unit_id)
            member = add_user_to_admin_unit_with_roles(user, admin_unit, role_names)
            self._db.session.commit()
            member_id = member.id

        return member_id

    def create_admin_unit_member_event_verifier(self, admin_unit_id):
        return self.create_admin_unit_member(admin_unit_id, ["event_verifier"])
