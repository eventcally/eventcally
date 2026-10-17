"""The fixture-only ORM helpers, branches the seeders do not reach."""


def test_insert_admin_unit_for_user_copies_logo_to_organizer(client, seeder, db, app):
    user_id = seeder.create_user()

    with app.app_context():
        from project.cli.seed_helpers import insert_admin_unit_for_user
        from project.models import AdminUnit, Image, User

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
        from project.cli.seed_helpers import (
            add_roles_to_admin_unit_member,
            add_user_to_admin_unit,
        )
        from project.models import AdminUnit, User

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        user = db.session.get(User, other_user_id)
        member = add_user_to_admin_unit(user, admin_unit)
        db.session.commit()

        add_roles_to_admin_unit_member(member, ["admin", "not-a-real-role"])
        db.session.commit()

        assert [role.name for role in member.roles] == ["admin"]


def test_upsert_event_category_creates_once(client, app, db):
    with app.app_context():
        from project.cli.seed_helpers import upsert_event_category
        from project.models import EventCategory

        first = upsert_event_category("Brand New")
        second = upsert_event_category("Brand New")

        assert first.id == second.id
        assert EventCategory.query.filter_by(name="Brand New").count() == 1
