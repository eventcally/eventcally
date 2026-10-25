def test_before_flush_of_empty_location_detaches_it_from_its_owners(app, mocker):
    from project.infrastructure.models import (
        AdminUnit,
        EventOrganizer,
        EventPlace,
        Location,
    )

    location = Location()
    admin_unit = AdminUnit(location=location)
    place = EventPlace(location=location)
    organizer = EventOrganizer(location=location)
    session = mocker.Mock()

    location.before_flush(session, is_dirty=True)

    assert admin_unit.location is None
    assert place.location is None
    assert organizer.location is None
    session.delete.assert_called_once_with(location)


def test_before_flush_of_new_location_is_not_deleted(app, mocker):
    from project.infrastructure.models import Location

    session = mocker.Mock()

    Location().before_flush(session, is_dirty=False)

    session.delete.assert_not_called()


def test_update_coordinate(app):
    from project.infrastructure.models import Location

    location = Location(latitude=52.5, longitude=13.4)
    location.update_coordinate()
    assert location.coordinate == "POINT(13.4 52.5)"

    location.latitude = None
    location.update_coordinate()
    assert location.coordinate is None
