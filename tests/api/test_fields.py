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


def test_numeric_str_deserialize(client, seeder, utils):
    from project.api.location.schemas import LocationPostRequestLoadSchema

    data = {
        "latitude": "51.9077888",
        "longitude": "10.4333312",
    }

    schema = LocationPostRequestLoadSchema()
    location = schema.load(data)

    assert location.latitude == 51.9077888
    assert location.longitude == 10.4333312


def test_numeric_str_deserialize_invalid(client, seeder, utils):
    from project.api.location.schemas import LocationPostRequestLoadSchema
    import pytest
    from marshmallow import ValidationError

    data = {
        "latitude": "Quatsch",
        "longitude": "Quatsch",
    }

    schema = LocationPostRequestLoadSchema()

    with pytest.raises(ValidationError):
        schema.load(data)
