"""SqlAlchemyAccessReadRepository against the database, on the read session."""

import pytest

from project.application.queries import ResourceKind
from tests.integration.event_read_seed import seed_event_world


@pytest.fixture
def world(app, db, seeder):
    return seed_event_world(app, db, seeder)


@pytest.fixture
def access(app, db):
    def call(method, *args):
        with app.app_context():
            repo = app.container.read_repos.access_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args)

    return call


def test_organization_flags_and_location(access, world):
    organization = access("get_organization", world["a"])

    assert organization.name == "Meine Crew"
    assert organization.short_name == "meinecrew"
    assert organization.is_verified is True
    assert organization.incoming_reference_requests_allowed is True
    assert organization.location.postalCode == "12345"
    assert access("get_organization", world["c"]).is_verified is False
    assert access("get_organization", 4711) is None


def test_organizations_are_listed_by_id_or_in_the_given_order(access, world):
    everything = access("list_organizations", None)
    chosen = access("list_organizations", [world["b"], world["a"], 4711])

    assert [o.id for o in everything] == sorted(o.id for o in everything)
    assert len(everything) >= 4
    assert [o.id for o in chosen] == [world["b"], world["a"]]


def test_member_organizations_in_membership_order(access, seeder, world):
    owner_id = seeder.get_admin_unit_owner_id(world["a"])
    seeder.create_admin_unit_member(world["b"], ["admin"], "test@test.de")

    assert access("member_organization_ids", owner_id) == [world["a"], world["b"]]
    assert access("member_organization_ids", 4711) == []


def test_resource_owners(app, db, seeder, access, world):
    from project.infrastructure.models import EventOrganizer

    with app.app_context():
        organizer_id = (
            EventOrganizer.query.filter_by(admin_unit_id=world["a"]).first().id
        )
    relation_source = world["b"]
    seeder.create_admin_unit_relation(relation_source, world["a"])
    request_id = seeder.create_reference_request(world["other"], world["a"])

    def owner(kind, resource_id):
        return access("get_resource_owner", kind, resource_id)

    assert owner(ResourceKind.event, world["full"]) == world["a"]
    assert owner(ResourceKind.event, world["other"]) == world["b"]
    assert owner(ResourceKind.event_organizer, organizer_id) == world["a"]
    assert owner(ResourceKind.event_place, world["rathaus"]) == world["a"]
    assert owner(ResourceKind.event_reference, world["reference"]) == world["a"]
    assert owner(ResourceKind.event_reference_request, request_id) == world["b"]
    assert owner(ResourceKind.event_reference_request_target, request_id) == world["a"]
    assert owner(ResourceKind.event, 4711) is None
    assert owner(ResourceKind.event_reference_request, 4711) is None


def test_resource_owner_of_the_outgoing_side_of_a_reference(app, db, access, world):
    from project.infrastructure.models import EventReference

    with app.app_context():
        reference = db.session.get(EventReference, world["reference"])
        event_owner_id = reference.event.admin_unit_id

    assert (
        access(
            "get_resource_owner",
            ResourceKind.event_reference_event_owner,
            world["reference"],
        )
        == event_owner_id
    )
    assert event_owner_id != world["a"]
    assert (
        access("get_resource_owner", ResourceKind.event_reference_event_owner, 4711)
        is None
    )


def test_resource_owners_of_relations_invitations_widgets_and_requests(
    app, db, seeder, access, world
):
    relation_id = seeder.create_admin_unit_relation(world["a"], world["c"])
    invitation_id = seeder.create_admin_unit_invitation(world["a"])
    widget_id = seeder.insert_event_custom_widget(world["a"])
    verification_id = seeder.create_admin_unit_verification_request(
        world["c"], world["b"]
    )

    def owner(kind, resource_id):
        return access("get_resource_owner", kind, resource_id)

    assert owner(ResourceKind.organization_relation, relation_id) == world["a"]
    assert owner(ResourceKind.organization_invitation, invitation_id) == world["a"]
    assert owner(ResourceKind.custom_widget, widget_id) == world["a"]
    assert (
        owner(ResourceKind.verification_request_source, verification_id) == world["c"]
    )
    assert (
        owner(ResourceKind.verification_request_target, verification_id) == world["b"]
    )


def test_other_admin(app, db, seeder, access, world):
    owner_id = seeder.get_admin_unit_owner_id(world["a"])

    assert access("has_other_admin", world["a"], owner_id) is False

    seeder.create_admin_unit_member(world["a"], ["admin"], "second@test.de")
    assert access("has_other_admin", world["a"], owner_id) is True

    seeder.create_admin_unit_member(world["b"], ["event_verifier"], "weak@test.de")
    assert access("has_other_admin", world["b"], 4711) is True  # the owner is admin


def test_api_key_by_hash(app, seeder, access, world):
    from project.shared.utils import hash_api_key

    owner_id = seeder.get_admin_unit_owner_id(world["a"])
    api_key_id, key = seeder.insert_default_api_key(owner_id)

    with app.app_context():
        key_hash = hash_api_key(key)
        unknown_hash = hash_api_key("unknown")

    api_key = access("get_api_key_by_hash", key_hash)

    assert api_key.id == api_key_id
    assert api_key.user_id == owner_id
    assert api_key.get_rate_limit_key() == f"apikey-{api_key_id}"
    assert access("get_api_key_by_hash", unknown_hash) is None


def test_name_uniqueness_ignores_case_and_the_excluded_organization(access, world):
    assert access("is_name_taken", "meine crew", None) is True
    assert access("is_name_taken", "meine crew", world["a"]) is False
    assert access("is_name_taken", "Nobody", None) is False
    assert access("is_short_name_taken", "MEINECREW", None) is True
    assert access("is_short_name_taken", "meinecrew", world["a"]) is False


def test_reference_requests_are_accepted_by_other_organizations(access, world):
    assert access("any_accepts_reference_requests", world["a"]) is True
    assert access("any_accepts_reference_requests", 4711) is True


def test_who_may_ask_whom_for_verification(app, db, seeder, access, world):
    from project.infrastructure.models import AdminUnit

    with app.app_context():
        for admin_unit_id in (world["b"],):
            admin_unit = db.session.get(AdminUnit, admin_unit_id)
            admin_unit.can_verify_other = True
            admin_unit.incoming_verification_requests_allowed = True
        db.session.commit()

    assert access("can_request_verification", world["c"], world["b"]) is True
    assert access("can_request_verification", world["b"], world["b"]) is False
    assert access("can_request_verification", world["c"], world["a"]) is False

    with app.app_context():
        db.session.get(
            AdminUnit, world["b"]
        ).incoming_verification_requests_postal_codes = ["99999"]
        db.session.commit()

    assert access("can_request_verification", world["c"], world["b"]) is False

    with app.app_context():
        db.session.get(
            AdminUnit, world["b"]
        ).incoming_verification_requests_postal_codes = ["12345"]
        db.session.commit()

    assert access("can_request_verification", world["c"], world["b"]) is True


def test_settings_carry_everything_the_forms_show(app, db, access, world):
    from project.infrastructure.models import AdminUnit

    with app.app_context():
        admin_unit = db.session.get(AdminUnit, world["a"])
        admin_unit.widget_font = "Arial"
        admin_unit.widget_primary_color = "#123456"
        admin_unit.url = "https://example.com"
        admin_unit.incoming_verification_requests_text = "Hello"
        admin_unit.incoming_verification_requests_postal_codes = ["386"]
        db.session.commit()

    settings = access("get_settings", world["a"])

    assert settings.name == "Meine Crew"
    assert settings.url == "https://example.com"
    assert settings.widget_font == "Arial"
    assert settings.widget_primary_color == "#123456"
    assert settings.widget_background_color is None
    assert settings.incoming_verification_requests_postal_codes == ["386"]
    assert settings.incoming_verification_requests_text == "Hello"
    assert settings.location.city == "City"
    assert settings.logo is None
    assert settings.deletion_requested_at is None
    assert access("get_settings", 4711) is None


def _set_review_status(app, db, model_name, request_id, status_name):
    with app.app_context():
        import project.infrastructure.models as models

        model = getattr(models, model_name)
        status = getattr(getattr(models, f"{model_name}ReviewStatus"), status_name)
        request = db.session.get(model, request_id)
        request.review_status = status
        db.session.commit()


def test_incoming_badges_count_inbox_requests_of_the_organization(
    access, app, db, seeder
):
    _, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("source@test.de")
    other_id = seeder.create_admin_unit(other_user_id, "Source Crew")
    first = seeder.create_reference_request(
        seeder.create_event(other_id), admin_unit_id
    )
    seeder.create_reference_request(seeder.create_event(other_id), admin_unit_id)
    seeder.create_reference_request(seeder.create_event(admin_unit_id), other_id)
    third_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Third Crew"
    )
    seeder.create_admin_unit_verification_request(other_id, admin_unit_id)
    done = seeder.create_admin_unit_verification_request(third_id, admin_unit_id)
    _set_review_status(app, db, "EventReferenceRequest", first, "verified")
    _set_review_status(app, db, "AdminUnitVerificationRequest", done, "rejected")

    badges = access("count_incoming_badges", admin_unit_id)

    assert badges.reference_requests_incoming_badge == 1
    assert badges.verification_requests_incoming_badge == 1
    assert (
        access("count_incoming_badges", other_id).reference_requests_incoming_badge == 1
    )
    assert (
        access("count_incoming_badges", 4711).verification_requests_incoming_badge == 0
    )


def test_event_report_recipients_are_writers_and_platform_admins(access, seeder):
    owner_id, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["event_verifier"], "ev@test.de")
    platform_admin_id = seeder.create_user("pa@test.de", admin=True, locale="en")
    seeder.create_user("plain@test.de")

    recipients = access("event_report_recipients", admin_unit_id, "events:write")

    assert [(r.email, r.locale) for r in recipients] == [
        ("test@test.de", None),
        ("ev@test.de", None),
        ("pa@test.de", "en"),
    ]
    assert [r.id for r in recipients] == sorted(r.id for r in recipients)
    assert platform_admin_id in [r.id for r in recipients]
    assert owner_id in [r.id for r in recipients]


def test_event_report_recipients_skip_members_without_the_permission(access, seeder):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["event_verifier"], "ev@test.de")

    recipients = access("event_report_recipients", admin_unit_id, "settings:write")

    assert [r.email for r in recipients] == ["test@test.de"]


def test_event_report_recipients_do_not_repeat_platform_admin_members(access, seeder):
    owner_id, admin_unit_id = seeder.setup_base(admin=True)

    recipients = access("event_report_recipients", admin_unit_id, "events:write")

    assert [r.id for r in recipients] == [owner_id]
