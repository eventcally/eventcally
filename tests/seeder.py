from tests.utils import UtilActions


class Seeder(object):
    def __init__(self, app, db, utils: UtilActions):
        self._app = app
        self._db = db
        self._utils = utils

    def setup_base(
        self,
        admin=False,
        log_in=True,
        admin_unit_verified=True,
        email="test@test.de",
        name="Meine Crew",
        password="MeinPasswortIstDasBeste",
    ):
        user_id = self.create_user(email=email, admin=admin)
        if log_in:
            self._utils.login(email, password)
        admin_unit_id = self.create_admin_unit(
            user_id, name=name, verified=admin_unit_verified
        )
        return (user_id, admin_unit_id)

    def setup_base_event_verifier(self):
        owner_id = self.create_user("owner@owner")
        admin_unit_id = self.create_admin_unit(owner_id, "Other crew")
        member_id = self.create_admin_unit_member_event_verifier(admin_unit_id)
        self._utils.login()
        return (owner_id, admin_unit_id, member_id)

    def create_user(
        self,
        email="test@test.de",
        password="MeinPasswortIstDasBeste",
        admin=False,
        confirm=True,
        tos_accepted=True,
        locale=None,
    ):
        from flask_security.confirmable import confirm_user

        from project.services.user import (
            add_admin_roles_to_user,
            create_user,
            find_user_by_email,
            set_user_accepted_tos,
        )

        with self._app.app_context():
            user = find_user_by_email(email)

            if user is None:
                user = create_user(email, password)

                if confirm:
                    confirm_user(user)

                if tos_accepted:
                    set_user_accepted_tos(user)

            if admin:
                add_admin_roles_to_user(email)

            user.locale = locale
            self._db.session.commit()
            user_id = user.id

        return user_id

    def create_admin_unit(
        self,
        user_id,
        name="Meine Crew",
        can_create_other=False,
        can_verify_other=False,
        verified=False,
        can_invite_other=True,
        incoming_verification_requests_allowed=False,
        **kwargs
    ):
        from project.models import AdminUnit, Location
        from project.services.admin_unit import insert_admin_unit_for_user
        from project.services.user import get_user

        with self._app.app_context():
            user = get_user(user_id)
            admin_unit = AdminUnit()
            admin_unit.name = name
            admin_unit.short_name = name.lower().replace(" ", "")
            admin_unit.incoming_reference_requests_allowed = True
            admin_unit.can_create_other = can_create_other
            admin_unit.can_verify_other = can_verify_other
            admin_unit.can_invite_other = can_invite_other
            admin_unit.incoming_verification_requests_allowed = (
                incoming_verification_requests_allowed
            )

            location = Location()
            location.postalCode = "12345"
            location.city = "City"
            admin_unit.location = location

            admin_unit.__dict__.update(kwargs)
            insert_admin_unit_for_user(admin_unit, user)
            self._db.session.commit()
            admin_unit_id = admin_unit.id

        if verified:
            self.verify_admin_unit(admin_unit_id)

        return admin_unit_id

    def get_eventcally_admin_unit_id(self):
        from project.services.admin_unit import get_admin_unit_by_name

        with self._app.app_context():
            other_admin_unit = get_admin_unit_by_name("eventcally")
            return other_admin_unit.id if other_admin_unit else None

    def verify_admin_unit(self, admin_unit_id):
        from project.services.admin_unit import get_admin_unit_by_name

        with self._app.app_context():
            other_admin_unit = get_admin_unit_by_name("eventcally")

            if other_admin_unit:
                other_admin_unit_id = other_admin_unit.id
            else:
                other_user_id = self.create_user("admin@eventcally.com")
                other_admin_unit_id = self.create_admin_unit(
                    other_user_id, "eventcally", can_verify_other=True
                )

            self.create_admin_unit_relation(
                other_admin_unit_id,
                admin_unit_id,
                verify=True,
            )

    def create_admin_unit_member(
        self,
        admin_unit_id,
        role_names,
        email="test@test.de",
    ):
        from project.services.admin_unit import (
            add_user_to_admin_unit_with_roles,
            get_admin_unit_by_id,
        )
        from project.services.user import get_user

        with self._app.app_context():
            user_id = self.create_user(email=email)
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

    def create_admin_unit_invitation(
        self,
        admin_unit_id,
        email="invited@test.de",
        admin_unit_name="Invited Organization",
        relation_auto_verify_event_reference_requests=False,
        relation_verify=False,
    ):
        from project.models import AdminUnitInvitation

        with self._app.app_context():
            invitation = AdminUnitInvitation()
            invitation.admin_unit_id = admin_unit_id
            invitation.email = email
            invitation.admin_unit_name = admin_unit_name
            invitation.relation_auto_verify_event_reference_requests = (
                relation_auto_verify_event_reference_requests
            )
            invitation.relation_verify = relation_verify
            self._db.session.add(invitation)
            self._db.session.commit()
            invitation_id = invitation.id

        return invitation_id

    def add_favorite_event(self, user_id, event_id):
        from project.services.user import add_favorite_event

        with self._app.app_context():
            if add_favorite_event(user_id, event_id):
                self._db.session.commit()

    def remove_favorite_event(self, user_id, event_id):
        from project.services.user import remove_favorite_event

        with self._app.app_context():
            if remove_favorite_event(user_id, event_id):
                self._db.session.commit()

    def create_admin_unit_member_event_verifier(
        self,
        admin_unit_id,
        email="test@test.de",
    ):
        return self.create_admin_unit_member(admin_unit_id, ["event_verifier"], email)

    def upsert_event_place(self, admin_unit_id, name, location=None):
        from project.services.place import upsert_event_place

        with self._app.app_context():
            place = upsert_event_place(admin_unit_id, name)

            if location:
                place.location = location

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

    def insert_event_custom_widget(
        self,
        admin_unit_id,
        widget_type="search",
        name="Mein Widget",
        settings={"color": "black"},
    ):
        from project.models import CustomWidget

        with self._app.app_context():
            custom_widget = CustomWidget()
            custom_widget.admin_unit_id = admin_unit_id
            custom_widget.widget_type = widget_type
            custom_widget.name = name
            custom_widget.settings = settings

            self._db.session.add(custom_widget)
            self._db.session.commit()
            custom_widget_id = custom_widget.id

        return custom_widget_id

    def insert_default_oauth2_client(self, user_id):
        from project.api import scope_list
        from project.models import OAuth2Client
        from project.services.oauth2_client import complete_oauth2_client

        with self._app.app_context():
            client = OAuth2Client()
            client.user_id = user_id
            complete_oauth2_client(client)

            metadata = dict()
            metadata["client_name"] = "Mein Client"
            metadata["scope"] = " ".join(scope_list)
            metadata["redirect_uris"] = [self._utils.get_url("swagger_oauth2_redirect")]
            client.set_client_metadata(metadata)

            self._db.session.add(client)
            self._db.session.commit()
            client_id = client.id

        return client_id

    def insert_default_api_key(self, user_id=None, admin_unit_id=None):
        from project.models import ApiKey

        with self._app.app_context():
            api_key = ApiKey()
            api_key.user_id = user_id
            api_key.admin_unit_id = admin_unit_id
            api_key.name = "Mein API Key"
            key = api_key.generate_key()

            self._db.session.add(api_key)
            self._db.session.commit()
            api_key_id = api_key.id

        return (api_key_id, key)

    def setup_api_access(
        self,
        admin=True,
        admin_unit_verified=True,
        user_access=True,
        email="test@test.de",
        admin_unit_name="Meine Crew",
        use_api_key=False,
    ):
        user_id, admin_unit_id = self.setup_base(
            admin, False, admin_unit_verified, email, admin_unit_name
        )

        if user_access:
            self.authorize_api_access(user_id, admin_unit_id)
        elif use_api_key:
            self.api_key_api_access(user_id)
        else:
            self.grant_client_credentials_api_access(user_id)

        return (user_id, admin_unit_id)

    def authorize_api_access(self, user_id, admin_unit_id, authorize_scope=None):
        oauth2_client_id = self.insert_default_oauth2_client(user_id)

        with self._app.app_context():
            from project.models import OAuth2Client
            from project.services.user import get_user

            user = get_user(user_id)
            email = user.email

            oauth2_client = self._db.session.get(OAuth2Client, oauth2_client_id)
            client_id = oauth2_client.client_id
            client_secret = oauth2_client.client_secret
            scope = oauth2_client.scope

        if authorize_scope:
            scope = authorize_scope

        self._utils.login(email=email)
        self._utils.authorize(client_id, client_secret, scope)
        self._utils.logout()
        return (user_id, admin_unit_id)

    def api_key_api_access(self, user_id):
        api_key_id, key = self.insert_default_api_key(user_id)
        self._utils.setup_api_key(key)

    def grant_client_credentials_api_access(self, user_id):
        oauth2_client_id = self.insert_default_oauth2_client(user_id)

        with self._app.app_context():
            from project.models import OAuth2Client

            oauth2_client = self._db.session.get(OAuth2Client, oauth2_client_id)
            client_id = oauth2_client.client_id
            client_secret = oauth2_client.client_secret
            scope = oauth2_client.scope

        self._utils.grant_client_credentials(client_id, client_secret, scope)

    def get_event_category_id(self, category_name):
        from project.services.event import get_event_category

        with self._app.app_context():
            category = get_event_category(category_name)

        return category.id

    def get_event_date_id(self, event_id):
        from project.models import Event

        with self._app.app_context():
            event = self._db.session.get(Event, event_id)
            event_date_id = event.dates[0].id

        return event_date_id

    def create_event(
        self,
        admin_unit_id,
        recurrence_rule="",
        external_link="",
        end=None,
        draft=False,
        name="Name",
        start=None,
        allday=False,
        co_organizer_ids=None,
        description="Beschreibung",
        tags="",
        place_id=None,
        planned=False,
        internal_tags="",
        **kwargs
    ):
        from project.models import (
            Event,
            EventAttendanceMode,
            EventOrganizer,
            PublicStatus,
        )
        from project.services.event import insert_event, upsert_event_category

        with self._app.app_context():
            event = Event()
            event.__dict__.update(kwargs)
            event.admin_unit_id = admin_unit_id
            event.categories = [upsert_event_category("Other")]
            event.name = name
            event.description = description
            event.organizer_id = self.upsert_default_event_organizer(admin_unit_id)
            event.external_link = external_link
            event.ticket_link = ""
            event.tags = tags
            event.internal_tags = internal_tags
            event.price_info = ""
            event.attendance_mode = EventAttendanceMode.offline

            if place_id:
                event.event_place_id = place_id
            else:
                event.event_place_id = self.upsert_default_event_place(admin_unit_id)

            date_definition = self.create_event_date_definition(
                start, end, allday, recurrence_rule
            )
            event.date_definitions = [date_definition]

            if planned:
                event.public_status = PublicStatus.planned

            if draft:
                event.public_status = PublicStatus.draft

            if co_organizer_ids:
                co_organizers = EventOrganizer.query.filter(
                    EventOrganizer.id.in_(co_organizer_ids)
                ).all()
                event.co_organizers = co_organizers

            insert_event(event)
            self._db.session.commit()
            event_id = event.id
        return event_id

    def create_event_date_definition(
        self, start=None, end=None, allday=False, recurrence_rule=""
    ):
        from project.models import EventDateDefinition

        with self._app.app_context():
            date_definition = EventDateDefinition()
            date_definition.start = start if start else self.get_now_by_minute()
            date_definition.end = end
            date_definition.allday = allday
            date_definition.recurrence_rule = recurrence_rule

            return date_definition

    def add_event_date_definition(
        self, event_id, start=None, end=None, allday=False, recurrence_rule=""
    ):
        from project.models import Event
        from project.services.event import update_event

        with self._app.app_context():
            event = self._db.session.get(Event, event_id)

            date_definition = self.create_event_date_definition(
                start, end, allday, recurrence_rule
            )
            date_definition.event = event
            self._db.session.add(date_definition)

            date_definitions = event.date_definitions
            date_definitions.append(date_definition)
            event.date_definitions = date_definitions
            update_event(event)
            self._db.session.commit()

            date_definition_id = date_definition.id

        return date_definition_id

    def create_event_unverified(self):
        user_id = self.create_user("unverified@test.de")
        admin_unit_id = self.create_admin_unit(user_id, "Unverified Crew")
        event_id = self.create_event(admin_unit_id)
        return (user_id, admin_unit_id, event_id)

    def create_event_with_co_organizers(self, admin_unit_id):
        organizer_a_id = self.upsert_event_organizer(admin_unit_id, "Organizer A")
        organizer_b_id = self.upsert_event_organizer(admin_unit_id, "Organizer B")
        event_id = self.create_event(
            admin_unit_id, co_organizer_ids=[organizer_a_id, organizer_b_id]
        )
        return (event_id, organizer_a_id, organizer_b_id)

    def create_event_via_form(self, admin_unit_id: int) -> str:
        place_id = self.upsert_default_event_place(admin_unit_id)
        organizer_id = self.upsert_default_event_organizer(admin_unit_id)
        url = self._utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
        response = self._utils.get_ok(url)
        response = self._utils.post_form(
            url,
            response,
            {
                "name": "Name",
                "description": "Beschreibung",
                "date_definitions-0-start": ["2030-12-31", "23:59"],
                "event_place": place_id,
                "organizer": organizer_id,
                "photo-image_base64": self.get_default_image_upload_base64(),
                "photo-copyright_text": "EventCally",
            },
        )

        with self._app.app_context():
            from project.models import Event

            event = (
                Event.query.filter(Event.admin_unit_id == admin_unit_id)
                .filter(Event.name == "Name")
                .first()
            )
            return event.id

    def create_event_via_api(self, admin_unit_id: int) -> int:
        place_id = self.upsert_default_event_place(admin_unit_id)
        organizer_id = self.upsert_default_event_organizer(admin_unit_id)

        url = self._utils.get_url("api_v1_organization_event_list", id=admin_unit_id)
        response = self._utils.post_json(
            url,
            {
                "name": "Name",
                "start": "2021-02-07T11:00:00.000Z",
                "place": {"id": place_id},
                "organizer": {"id": organizer_id},
            },
        )
        self._utils.assert_response_created(response)
        assert "id" in response.json
        return response.json["id"]

    def get_default_image_base64(self):
        return """iVBORw0KGgoAAAANSUhEUgAAAUAAAAFABAMAAAA/vriZAAAAG1BMVEUAAAD///9fX1+fn5+/v7/f398/Pz8fHx9/f38YYyahAAAACXBIWXMAAA7EAAAOxAGVKw4bAAADAklEQVR4nO3XzVPaQBzG8RQw4dhosB6hdexVhPZM6lg9mlrGHkFH7RGmhfYIM53aP7v7lhBeNgqul/b7OZBNzOPu/DbZBc8DAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8O97c9I97qlWqd39fO+lzbOBNSJvfO+tl9lU0AyPW3Ek//G3MDo+CSfyqp9E7WTPlhE3ttrhqbdOZmPlnZ4Y5fRSNJuyKDeqi/626DA+tGTUjT9rg3UyG/PVpPiR+HgrW0EiB6w6r9jKcac++511Mk8VZw9PQ9SgvKuaSeETVXmVNR+d2dy0l7ZenHvesKP7nRRFqrtZ89GZzc0GWHkpzuq6305RJDfAR2c2F891ZiY8ncRqTx9fz0XkjfaMY/5O1twS09U1AzM1GuljKZrL9A+LMo7dXGZN8SwFZiSlbX1Ub6l4vE7zEb87KMq4dR3NOmvUPd+sFelRl7AU5V9Qv5kb7qqMw9G1TqL67DSZdRKkE69KmCug32onH7zijDvTMLyYDbC6t6ozUcJ8AathWDvyHsg4NN6vZSMcnq/qTJRw/gkMruJPXnHGqe/Zox33VnY22osWtoggrj+QcSrdocpypCs6C5LLxchWuuLZMk6lO1Rzkusk90aWwqX1rZT+1ZZxyuxQVd3N8prW+KjXwjxzlzXzHAOc6t0h0RfL2bYlXuHRUgnNkGyZ5xigKYbX7KmD3ME08QoHSyXUA7Rm3BqqMjTN9tqf6EO626o1cLGE5qmzZRyb1j359d+cmRfUFMVsIoslrKqnzZpxK6jJj3hiTkuq1+zbi9lEFkool2d7xpmtuvy8kX2PZi+gmrdGuvQN9SYSmG9UntpDfFVQa8aZSu3o7vZXWJdTePZHuldXf4v9r2fu8c0q/sOcxxcH46+xHJo94851InZ+2UEQamoi98XFiS3ivxO3fRmslXmC4Op2xS+x8UHRz7Pxwd3Kq8/0kw4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4L/0FiGF8UcQrzsIAAAAASUVORK5CYII="""

    def get_default_image_upload_base64(self):
        base64_str = self.get_default_image_base64()
        return "data:image/png;base64,{}".format(base64_str)

    def upsert_default_image(self):
        from project.services.image import upsert_image_with_base64_str

        with self._app.app_context():
            base64_str = self.get_default_image_base64()
            image = upsert_image_with_base64_str(None, base64_str, "image/png")
            self._db.session.add(image)
            self._db.session.commit()
            image_id = image.id

        return image_id

    def assign_image_to_event(self, event_id, image_id):
        with self._app.app_context():
            from project.models import Event

            event = self._db.session.get(Event, event_id)
            event.photo_id = image_id
            self._db.session.commit()

    def add_event_to_list(self, event_list_id, event_id):
        from project.models import Event, EventList

        with self._app.app_context():
            event = self._db.session.get(Event, event_id)
            event_list = self._db.session.get(EventList, event_list_id)
            event_list.events.append(event)
            self._db.session.commit()

    def create_event_list(self, admin_unit_id, event_ids=list(), name="My list"):
        from project.models import EventList

        with self._app.app_context():
            event_list = EventList()
            event_list.name = name
            event_list.admin_unit_id = admin_unit_id
            self._db.session.add(event_list)
            self._db.session.commit()
            event_list_id = event_list.id

        if type(event_ids) is not list:
            event_ids = [event_ids]

        for event_id in event_ids:
            self.add_event_to_list(event_list_id, event_id)

        return event_list_id

    def create_reference(self, event_id, admin_unit_id):
        from project.models import EventReference

        with self._app.app_context():
            reference = EventReference()
            reference.event_id = event_id
            reference.admin_unit_id = admin_unit_id
            self._db.session.add(reference)
            self._db.session.commit()
            reference_id = reference.id
        return reference_id

    def create_any_reference(self, admin_unit_id):
        (other_user_id, other_admin_unit_id) = self.setup_base(
            email="other@test.de", name="Other Crew", log_in=False
        )
        event_id = self.create_event(other_admin_unit_id)
        reference_id = self.create_reference(event_id, admin_unit_id)
        return (other_user_id, other_admin_unit_id, event_id, reference_id)

    def create_admin_unit_relation(
        self,
        admin_unit_id,
        target_admin_unit_id,
        auto_verify_event_reference_requests=False,
        verify=False,
    ):
        from project.services.admin_unit import upsert_admin_unit_relation

        with self._app.app_context():
            relation = upsert_admin_unit_relation(admin_unit_id, target_admin_unit_id)
            relation.auto_verify_event_reference_requests = (
                auto_verify_event_reference_requests
            )
            relation.verify = verify
            self._db.session.commit()
            relation_id = relation.id

        return relation_id

    def create_any_admin_unit_relation(
        self,
        admin_unit_id,
        admin_unit_name="Other Crew",
        auto_verify_event_reference_requests=False,
        verify=False,
    ):
        other_user_id = self.create_user("other@test.de")
        other_admin_unit_id = self.create_admin_unit(other_user_id, admin_unit_name)
        relation_id = self.create_admin_unit_relation(
            admin_unit_id,
            other_admin_unit_id,
            auto_verify_event_reference_requests,
            verify,
        )
        return (other_user_id, other_admin_unit_id, relation_id)

    def setup_admin_unit_missing_verification_scenario(
        self, log_in_verifier=False, api=False
    ):
        verifier_user_id = self.create_user()
        verifier_admin_unit_id = self.create_admin_unit(
            verifier_user_id,
            "Stadtmarketing",
            verified=True,
            can_verify_other=True,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_text="Please give us a call",
        )

        if api:
            unverified_user_id, unverified_admin_unit_id = self.setup_api_access(
                admin=False,
                admin_unit_verified=False,
                email="mitglied@verein.de",
                admin_unit_name="Verein",
            )

            if log_in_verifier:
                self.authorize_api_access(verifier_user_id, verifier_admin_unit_id)
        else:
            unverified_user_id, unverified_admin_unit_id = self.setup_base(
                log_in=not log_in_verifier,
                admin_unit_verified=False,
                email="mitglied@verein.de",
                name="Verein",
            )

            if log_in_verifier:
                self._utils.login()

        return (
            verifier_user_id,
            verifier_admin_unit_id,
            unverified_user_id,
            unverified_admin_unit_id,
        )

    def create_admin_unit_verification_request(
        self, source_admin_unit_id, target_admin_unit_id
    ):
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        with self._app.app_context():
            from project.services.admin_unit import get_admin_unit_by_id

            target_admin_unit = get_admin_unit_by_id(target_admin_unit_id)
            target_admin_unit.can_verify_other = True
            target_admin_unit.incoming_verification_requests_allowed = True

            request = AdminUnitVerificationRequest()
            request.source_admin_unit_id = source_admin_unit_id
            request.target_admin_unit_id = target_admin_unit_id
            request.review_status = AdminUnitVerificationRequestReviewStatus.inbox
            self._db.session.add(request)
            self._db.session.commit()
            request_id = request.id
        return request_id

    def create_incoming_admin_unit_verification_request(self, admin_unit_id):
        other_user_id = self.create_user("other@test.de")
        other_admin_unit_id = self.create_admin_unit(
            other_user_id, "Other Crew", verified=False
        )
        request_id = self.create_admin_unit_verification_request(
            other_admin_unit_id, admin_unit_id
        )
        return (other_user_id, other_admin_unit_id, request_id)

    def create_reference_request(self, event_id, admin_unit_id):
        from project.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        with self._app.app_context():
            reference_request = EventReferenceRequest()
            reference_request.event_id = event_id
            reference_request.admin_unit_id = admin_unit_id
            reference_request.review_status = EventReferenceRequestReviewStatus.inbox
            self._db.session.add(reference_request)
            self._db.session.commit()
            reference_request_id = reference_request.id
        return reference_request_id

    def create_incoming_reference_request(self, admin_unit_id):
        other_user_id = self.create_user("other@test.de")
        other_admin_unit_id = self.create_admin_unit(other_user_id, "Other Crew")
        event_id = self.create_event(other_admin_unit_id)
        reference_request_id = self.create_reference_request(event_id, admin_unit_id)
        return (other_user_id, other_admin_unit_id, event_id, reference_request_id)

    def create_outgoing_reference_request(self, admin_unit_id):
        other_user_id = self.create_user("other@test.de")
        other_admin_unit_id = self.create_admin_unit(other_user_id, "Other Crew")
        event_id = self.create_event(admin_unit_id)
        reference_request_id = self.create_reference_request(
            event_id, other_admin_unit_id
        )
        return (other_user_id, other_admin_unit_id, event_id, reference_request_id)

    def get_now_by_minute(self):
        from datetime import datetime

        from project.dateutils import get_now

        now = get_now()
        return datetime(
            now.year, now.month, now.day, now.hour, now.minute, tzinfo=now.tzinfo
        )

    def create_common_scenario(self):
        from dateutil.relativedelta import relativedelta

        from project.models import Location

        with self._app.app_context():
            now = self.get_now_by_minute()

            # Admin with eventcally organisation
            admin_id = self.create_user(
                "admin@test.de", "MeinPasswortIstDasBeste", admin=True
            )
            eventcally_admin_unit_id = self.create_admin_unit(
                admin_id,
                "eventcally",
                can_create_other=True,
                can_verify_other=True,
                verified=False,
                can_invite_other=True,
            )

            # User with verified Stadtmarketing organisation
            user_id = self.create_user("test@test.de", "MeinPasswortIstDasBeste")
            marketing_admin_unit_id = self.create_admin_unit(
                user_id,
                "Stadtmarketing",
                can_verify_other=True,
                incoming_verification_requests_allowed=True,
                incoming_verification_requests_text="Please give us a call",
            )
            self.create_admin_unit_relation(
                eventcally_admin_unit_id,
                marketing_admin_unit_id,
                verify=True,
            )
            self.create_event(marketing_admin_unit_id)
            self.create_event(
                marketing_admin_unit_id,
                recurrence_rule="RRULE:FREQ=DAILY;COUNT=7",
                name="Recurring",
                start=now,
                end=now + relativedelta(hours=1),
                place_id=self.upsert_event_place(
                    marketing_admin_unit_id,
                    "MachmitHaus",
                    Location(
                        street="Markt 7",
                        postalCode="38640",
                        city="Goslar",
                        latitude=51.9077888,
                        longitude=10.4333312,
                    ),
                ),
            )

            # Unverified Verein organisation
            verein_admin_unit_id = self.create_admin_unit(
                user_id,
                "Verein",
            )
            self.create_event(verein_admin_unit_id)

    def create_location(
        self,
        street=None,
        postalCode=None,
        city=None,
        latitude=None,
        longitude=None,
    ):
        from project.models import Location

        with self._app.app_context():
            location = Location(
                street=street,
                postalCode=postalCode,
                city=city,
                latitude=latitude,
                longitude=longitude,
            )
            self._db.session.add(location)
            self._db.session.commit()
            location_id = location.id

        return location_id
