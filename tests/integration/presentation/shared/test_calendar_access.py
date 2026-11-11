import pytest


@pytest.fixture
def calendar_organization(app):
    def call(user_id=None):
        from flask_login import login_user

        from project.infrastructure.user_datastore import get_user
        from project.presentation.shared.calendar_access import calendar_organization

        with app.test_request_context():
            if user_id is not None:
                login_user(get_user(user_id))

            admin_unit = calendar_organization()
            return admin_unit and admin_unit.id

    return call


def test_anonymous_visitors_have_no_calendar_organization(calendar_organization):
    assert calendar_organization() is None


def test_member_with_calendars_has_the_organization(
    app, client, seeder, calendar_organization
):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_calendar(admin_unit_id)

    assert calendar_organization(user_id) == admin_unit_id


def test_organization_without_calendars_is_none(seeder, calendar_organization):
    user_id, _ = seeder.setup_base(log_in=False)

    assert calendar_organization(user_id) is None


def test_member_without_write_permission_is_none(seeder, app, calendar_organization):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_calendar(admin_unit_id)
    seeder.create_admin_unit_member(admin_unit_id, [], email="member@test.de")
    with app.app_context():
        from project.infrastructure.user_datastore import find_user_by_email

        member_id = find_user_by_email("member@test.de").id

    assert calendar_organization(member_id) is None


def test_user_without_organization_is_none(seeder, calendar_organization):
    user_id = seeder.create_user("lonely@test.de")

    assert calendar_organization(user_id) is None
