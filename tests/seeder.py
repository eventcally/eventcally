class Seeder(object):
    def __init__(self, app, db, utils):
        self._app = app
        self._db = db
        self._utils = utils

    def setup_base(self):
        user_id = self.create_user()
        self._utils.login()
        admin_unit_id = self.create_admin_unit(user_id, "Meine Crew")
        return (user_id, admin_unit_id)

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

    def create_invitation(self, admin_unit_id, email, role_names=["admin"]):
        from project.services.admin_unit import insert_admin_unit_member_invitation

        with self._app.app_context():
            invitation = insert_admin_unit_member_invitation(
                admin_unit_id, email, role_names
            )
            invitation_id = invitation.id

        return invitation_id

    def create_admin_unit_member_event_verifier(self, admin_unit_id):
        return self.create_admin_unit_member(admin_unit_id, ["event_verifier"])

    def upsert_event_place(self, admin_unit_id, name):
        from project.services.place import upsert_event_place

        with self._app.app_context():
            place = upsert_event_place(admin_unit_id, name)
            self._db.session.commit()
            place_id = place.id

        return place_id

    def upsert_default_event_place(self, admin_unit_id):
        from project.services.admin_unit import get_admin_unit_by_id

        with self._app.app_context():
            admin_unit = get_admin_unit_by_id(admin_unit_id)
            place_id = self.upsert_event_place(admin_unit_id, admin_unit.name)

        return place_id

    def upsert_event_organizer(self, admin_unit_id, name):
        from project.services.organizer import upsert_event_organizer

        with self._app.app_context():
            organizer = upsert_event_organizer(admin_unit_id, name)
            self._db.session.commit()
            organizer_id = organizer.id

        return organizer_id

    def upsert_default_event_organizer(self, admin_unit_id):
        from project.services.admin_unit import get_admin_unit_by_id

        with self._app.app_context():
            admin_unit = get_admin_unit_by_id(admin_unit_id)
            organizer_id = self.upsert_event_organizer(admin_unit_id, admin_unit.name)

        return organizer_id

    def create_event(self, admin_unit_id):
        from project.models import Event
        from project.services.event import insert_event, upsert_event_category
        from project.dateutils import now

        with self._app.app_context():
            event = Event()
            event.admin_unit_id = admin_unit_id
            event.categories = [upsert_event_category("Other")]
            event.name = "Name"
            event.description = "Beschreibung"
            event.start = now
            event.event_place_id = self.upsert_default_event_place(admin_unit_id)
            event.organizer_id = self.upsert_default_event_organizer(admin_unit_id)
            insert_event(event)
            self._db.session.commit()
            event_id = event.id
        return event_id

    def create_event_suggestion(self, admin_unit_id):
        from project.models import EventSuggestion
        from project.services.event_suggestion import insert_event_suggestion
        from project.dateutils import now

        with self._app.app_context():
            suggestion = EventSuggestion()
            suggestion.admin_unit_id = admin_unit_id
            suggestion.contact_name = "Vorname Nachname"
            suggestion.contact_email = "vorname@nachname.de"
            suggestion.name = "Vorschlag"
            suggestion.description = "Beschreibung"
            suggestion.start = now
            suggestion.event_place_id = self.upsert_default_event_place(admin_unit_id)
            suggestion.organizer_id = self.upsert_default_event_organizer(admin_unit_id)
            insert_event_suggestion(suggestion)
            self._db.session.commit()
            suggestion_id = suggestion.id
        return suggestion_id
