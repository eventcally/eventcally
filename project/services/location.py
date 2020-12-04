def assign_location_values(target, origin):
    if origin:
        target.street = origin.street
        target.postalCode = origin.postalCode
        target.city = origin.city
        target.state = origin.state
        target.country = origin.country
        target.latitude = origin.latitude
        target.longitude = origin.longitude
