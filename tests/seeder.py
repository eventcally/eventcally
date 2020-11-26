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

    def upsert_default_image(self):
        from project.services.image import upsert_image_with_base64_str

        with self._app.app_context():
            base64_str = """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"""
            image = upsert_image_with_base64_str(None, base64_str, "image/png")
            self._db.session.add(image)
            self._db.session.commit()
            image_id = image.id

        return image_id

    def create_event_suggestion(self, admin_unit_id, free_text=False):
        from project.models import EventSuggestion
        from project.services.event_suggestion import insert_event_suggestion
        from project.dateutils import now

        with self._app.app_context():
            suggestion = EventSuggestion()
            suggestion.admin_unit_id = admin_unit_id
            suggestion.contact_name = "Vorname Nachname"
            suggestion.contact_email = "vorname@nachname.de"
            suggestion.contact_email_notice = True
            suggestion.name = "Vorschlag"
            suggestion.description = "Beschreibung"
            suggestion.start = now
            suggestion.photo_id = self.upsert_default_image()

            if free_text:
                suggestion.event_place_text = "Freitext Ort"
                suggestion.organizer_text = "Freitext Organisator"
            else:
                suggestion.event_place_id = self.upsert_default_event_place(
                    admin_unit_id
                )
                suggestion.organizer_id = self.upsert_default_event_organizer(
                    admin_unit_id
                )
            insert_event_suggestion(suggestion)
            self._db.session.commit()
            suggestion_id = suggestion.id
        return suggestion_id
