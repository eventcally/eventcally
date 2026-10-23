from project.presentation.shared.maputils import get_gmaps_place_address


def test_address_without_components():
    address = get_gmaps_place_address(
        {"geometry": {"location": {"lat": 1.5, "lng": 2.5}}}
    )

    assert address == {
        "street": "",
        "city": "",
        "state": "",
        "postalCode": "",
        "latitude": 1.5,
        "longitude": 2.5,
    }
