def test_get_location_str_none(client, seeder, app, utils):
    from project.utils import get_location_str

    location_str = get_location_str(None)
    assert location_str == ""


def test_get_location_str_empty(client, seeder, app, utils):
    from project.models import Location
    from project.utils import get_location_str

    location = Location()

    location_str = get_location_str(location)
    assert location_str == ""


def test_get_location_str_full(client, seeder, app, utils):
    from project.models import Location
    from project.utils import get_location_str

    location = Location()
    location.street = "Strasse"
    location.postalCode = "PLZ"
    location.city = "Ort"

    location_str = get_location_str(location)
    assert location_str == "Strasse, PLZ Ort"


def test_get_location_str_no_street(client, seeder, app, utils):
    from project.models import Location
    from project.utils import get_location_str

    location = Location()
    location.postalCode = "PLZ"
    location.city = "Ort"

    location_str = get_location_str(location)
    assert location_str == "PLZ Ort"


def test_get_place_str_full(client, seeder, app, utils):
    from project.models import EventPlace, Location
    from project.utils import get_place_str

    place = EventPlace()
    place.name = "Name"
    place.location = Location()
    place.location.street = "Strasse"
    place.location.postalCode = "PLZ"
    place.location.city = "Ort"

    place_str = get_place_str(place)
    assert place_str == "Name, Strasse, PLZ Ort"


def test_get_place_str_none(client, seeder, app, utils):
    from project.utils import get_place_str

    place_str = get_place_str(None)
    assert place_str == ""


def test_get_place_str_no_location(client, seeder, app, utils):
    from project.models import EventPlace
    from project.utils import get_place_str

    place = EventPlace()
    place.name = "Name"

    place_str = get_place_str(place)
    assert place_str == "Name"
