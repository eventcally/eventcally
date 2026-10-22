from flask_babel import lazy_gettext

# (value in metres, label) of the radius selects next to a location filter.
distance_choices = [
    (500, lazy_gettext("500 m")),
    (5000, lazy_gettext("5 km")),
    (10000, lazy_gettext("10 km")),
    (25000, lazy_gettext("20 km")),
    (50000, lazy_gettext("50 km")),
    (100000, lazy_gettext("100 km")),
]
