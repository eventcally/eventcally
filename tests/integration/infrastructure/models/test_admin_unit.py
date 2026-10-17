def test_fill_from_aggregate_clears_existing_location(app):
    with app.app_context():
        from project.domain.models.aggregates.organization_aggregate import (
            OrganizationAggregate,
        )
        from project.models import AdminUnit, Location

        model = AdminUnit()
        model.location = Location(city="Goslar")

        aggregate = OrganizationAggregate(
            id=-1, name="Org", short_name="org", location=None
        )
        model.fill_from_aggregate(aggregate)

        assert model.location is None
