"""The fixture-only ORM helpers, branches the seeders do not reach."""


def test_insert_admin_unit_for_user_copies_logo_to_organizer(client, seeder, db, app):
    user_id = seeder.create_user()

    with app.app_context():
        from project.infrastructure.models import AdminUnit, Image, User
        from project.infrastructure.seed_helpers import insert_admin_unit_for_user

        user = db.session.get(User, user_id)
        admin_unit = AdminUnit()
        admin_unit.name = "Logo Crew"
        admin_unit.short_name = "logo_crew"
        admin_unit.logo = Image(
            data=b"x", encoding_format="image/png", copyright_text="EventCally"
        )

        organizer, place = insert_admin_unit_for_user(admin_unit, user)

        assert organizer.logo.data == b"x"
        assert organizer.logo.encoding_format == "image/png"


def test_add_roles_to_admin_unit_member_skips_unknown_role(client, seeder, db, app):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")

    with app.app_context():
        from project.infrastructure.models import AdminUnit, User
        from project.infrastructure.seed_helpers import (
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


def test_upsert_event_category_creates_once(client, app, db):
    with app.app_context():
        from project.infrastructure.models import EventCategory
        from project.infrastructure.seed_helpers import upsert_event_category

        first = upsert_event_category("Brand New")
        second = upsert_event_category("Brand New")

        assert first.id == second.id
        assert EventCategory.query.filter_by(name="Brand New").count() == 1


def test_member_and_invitation_lookups(client, seeder, db, app):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")

    with app.app_context():
        from project.infrastructure.models import AdminUnit, User
        from project.infrastructure.seed_helpers import (
            add_user_to_admin_unit,
            find_admin_unit_member_invitation,
            get_admin_unit_member,
            get_member_for_admin_unit_by_user_id,
            insert_admin_unit_member_invitation,
        )

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        member = add_user_to_admin_unit(db.session.get(User, other_user_id), admin_unit)
        invitation = insert_admin_unit_member_invitation(
            admin_unit_id, "Invited@test.de", ["admin"]
        )
        db.session.commit()

        assert get_admin_unit_member(member.id).user_id == other_user_id
        assert (
            get_member_for_admin_unit_by_user_id(admin_unit_id, other_user_id).id
            == member.id
        )
        assert get_member_for_admin_unit_by_user_id(admin_unit_id, 4711) is None
        found = find_admin_unit_member_invitation("invited@TEST.de", admin_unit_id)
        assert found.id == invitation.id
        assert (
            find_admin_unit_member_invitation("nobody@test.de", admin_unit_id) is None
        )
        assert user_id != other_user_id


def test_delete_admin_unit_removes_it(client, seeder, db, app):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Doomed Crew")

    with app.app_context():
        from project.infrastructure.seed_helpers import (
            delete_admin_unit,
            get_admin_unit_by_id,
        )

        delete_admin_unit(get_admin_unit_by_id(admin_unit_id))

        assert get_admin_unit_by_id(admin_unit_id) is None


def test_event_category_lookups(client, db, app):
    with app.app_context():
        from project.infrastructure.seed_helpers import (
            get_event_category,
            upsert_event_category,
        )

        assert get_event_category("Seed Category") is None
        category = upsert_event_category("Seed Category")

        assert get_event_category("Seed Category").id == category.id
        assert upsert_event_category("Seed Category").id == category.id


def test_reset_tos_accepted_for_users_clears_the_timestamp(client, seeder, db, app):
    user_id = seeder.create_user()

    with app.app_context():
        import datetime

        from project.infrastructure.models import User
        from project.infrastructure.seed_helpers import reset_tos_accepted_for_users

        user = db.session.get(User, user_id)
        user.tos_accepted_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()

        reset_tos_accepted_for_users()

        db.session.expire_all()
        assert db.session.get(User, user_id).tos_accepted_at is None
