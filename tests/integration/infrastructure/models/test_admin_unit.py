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
