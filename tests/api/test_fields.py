import pytest


def test_numeric_str_serialize(client, seeder, utils):
    from project.api.location.schemas import LocationSchema
    from project.models import Location

    location = Location()
    location.street = "Markt 7"
    location.postalCode = "38640"
    location.city = "Goslar"
    location.latitude = 51.9077888
    location.longitude = 10.4333312

    schema = LocationSchema()
    data = schema.dump(location)

    assert data["latitude"] == "51.9077888"
    assert data["longitude"] == "10.4333312"


@pytest.mark.parametrize(
    "latitude, longitude, valid",
    [
        ("51.9077888", "10.4333312", True),
        ("-89.9", "0", True),
        ("-90", "0", False),
        ("0", "179.9", True),
        ("0", "180", False),
        ("0", None, False),
        (None, "0", False),
        ("Quatsch", "Quatsch", False),
    ],
)
def test_numeric_str_deserialize(latitude, longitude, valid):
    from project.api.location.schemas import LocationPostRequestSchema
    from marshmallow import ValidationError

    data = {
        "latitude": latitude,
        "longitude": longitude,
    }

    schema = LocationPostRequestSchema()

    if valid:
        location = schema.load(data)
        assert location.latitude == float(latitude)
        assert location.longitude == float(longitude)
        return

    with pytest.raises(ValidationError):
        schema.load(data)
