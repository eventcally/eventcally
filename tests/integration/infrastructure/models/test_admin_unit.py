def test_fill_from_aggregate_clears_existing_location(app):
    with app.app_context():
        from project.domain.models.aggregates.organization_aggregate import (
            OrganizationAggregate,
        )
        from project.infrastructure.models import AdminUnit, Location

        model = AdminUnit()
        model.location = Location(city="Goslar")

        aggregate = OrganizationAggregate(
            id=-1, name="Org", short_name="org", location=None
        )
        model.fill_from_aggregate(aggregate)

        assert model.location is None


def test_to_aggregate_converts_widget_colors(app):
    with app.app_context():
        from colour import Color

        from project.infrastructure.models import AdminUnit

        model = AdminUnit(
            id=1,
            name="Org",
            short_name="org",
            can_verify_other=False,
            can_create_other=False,
            can_invite_other=False,
            incoming_verification_requests_allowed=False,
            max_api_keys=1,
            widget_background_color=Color("#eceef0"),
            widget_primary_color=Color("#ffffff"),
            widget_link_color=None,
        )

        aggregate = AdminUnit.to_aggregate(model)

        assert aggregate.widget_background_color == "#eceef0"
        assert aggregate.widget_primary_color == "#ffffff"
        assert aggregate.widget_link_color is None


def test_relation_validate_rejects_self_reference(app):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from project.infrastructure.models import AdminUnitRelation

    with pytest.raises(IntegrityError) as e:
        AdminUnitRelation(source_admin_unit_id=1, target_admin_unit_id=1).validate()
    assert e.value.orig.message == "There must be no self-reference."

    AdminUnitRelation(source_admin_unit_id=1, target_admin_unit_id=2).validate()


def test_fill_from_aggregate_creates_logo(app):
    from project.domain.models.aggregates.organization_aggregate import (
        OrganizationAggregate,
    )
    from project.domain.models.entities.image_entity import ImageEntity
    from project.infrastructure.models import AdminUnit

    aggregate = OrganizationAggregate(
        id=-1,
        name="Org",
        short_name="org",
        logo=ImageEntity.model_construct(
            id=-1,
            hash=1,
            data=b"logo",
            encoding_format="image/png",
            copyright_text="Copyright",
            license_id=None,
        ),
    )
    model = AdminUnit()

    model.fill_from_aggregate(aggregate)

    assert model.logo.data == b"logo"


def test_is_verified_needs_a_verifying_incoming_relation(app, db, seeder):
    from project.infrastructure.models import AdminUnit

    seeder.setup_base(log_in=False)
    target_id = seeder.create_admin_unit(seeder.create_user("t@test.de"), "Target Crew")
    verifier_id = seeder.create_admin_unit(
        seeder.create_user("v@test.de"), "Verifier Crew", can_verify_other=True
    )
    other_id = seeder.create_admin_unit(seeder.create_user("o@test.de"), "Other Crew")

    with app.app_context():
        assert db.session.get(AdminUnit, target_id).is_verified is False

    seeder.create_admin_unit_relation(verifier_id, target_id, verify=True)
    seeder.create_admin_unit_relation(other_id, verifier_id, verify=True)

    with app.app_context():
        assert db.session.get(AdminUnit, target_id).is_verified is True
        assert db.session.get(AdminUnit, verifier_id).is_verified is False


def test_disabling_can_invite_other_drops_open_invitations(app, db, seeder):
    from project.infrastructure.models import AdminUnit

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_admin_unit_invitation(admin_unit_id, "invited@test.de")

    with app.app_context():
        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert len(admin_unit.admin_unit_invitations) == 1

        admin_unit.can_invite_other = False

        assert admin_unit.admin_unit_invitations == []
