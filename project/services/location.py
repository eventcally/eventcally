from project.models import Location

def upsert_location(street, postalCode, city, latitude = 0, longitude = 0, state = None):
    result = Location.query.filter_by(street = street, postalCode=postalCode, city=city, state=state).first()
    if result is None:
        result = Location(street = street, postalCode=postalCode, city=city, state=state)
        db.session.add(result)

    result.latitude = latitude
    result.longitude = longitude

    return result


def assign_location_values(target, origin):
    if origin:
        target.street = origin.street
        target.postalCode = origin.postalCode
        target.city = origin.city
        target.state = origin.state
        target.country = origin.country
        target.latitude = origin.latitude
        target.longitude = origin.longitude