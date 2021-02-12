import os
from urllib.parse import quote_plus

from project import app
from project.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_localized_scope,
)


def env_override(value, key):
    return os.getenv(key, value)


def is_list(value):
    return isinstance(value, list)


app.jinja_env.filters["event_category_name"] = lambda u: get_event_category_name(u)
app.jinja_env.filters["loc_enum"] = lambda u: get_localized_enum_name(u)
app.jinja_env.filters["loc_scope"] = lambda s: get_localized_scope(s)
app.jinja_env.filters["env_override"] = env_override
app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
app.jinja_env.filters["is_list"] = is_list


@app.context_processor
def get_manage_menu_options_context_processor():
    def get_manage_menu_options(admin_unit):
        from project.access import has_access
        from project.services.event_suggestion import get_event_reviews_badge_query
        from project.services.reference import (
            get_reference_requests_incoming_badge_query,
        )

        reviews_badge = 0
        reference_requests_incoming_badge = get_reference_requests_incoming_badge_query(
            admin_unit
        ).count()

        if has_access(admin_unit, "event:verify"):
            reviews_badge = get_event_reviews_badge_query(admin_unit).count()

        return {
            "reviews_badge": reviews_badge,
            "reference_requests_incoming_badge": reference_requests_incoming_badge,
        }

    return dict(get_manage_menu_options=get_manage_menu_options)
