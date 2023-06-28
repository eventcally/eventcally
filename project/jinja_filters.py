import os
from urllib.parse import quote_plus

from flask import url_for

from project import app
from project.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_localized_scope,
    get_location_str,
    get_place_str,
)


def env_override(value, key):
    return os.getenv(key, value)


def is_list(value):
    return isinstance(value, list)


def js_bool(value):
    return "true" if value else "false"


def any_dict_value_true(data: dict):
    return any(data.values())


def ensure_link_scheme(link: str):
    if not link:  # pragma: no cover
        return link

    if link.startswith("http://") or link.startswith("https://"):
        return link

    return f"https://{link}"


def human_file_size(bytes, units=[" bytes", "KB", "MB", "GB", "TB", "PB", "EB"]):
    return (
        str(bytes) + units[0]
        if bytes < 1024
        else human_file_size(bytes >> 10, units[1:])
        if units[1:]
        else f"{bytes>>10}ZB"
    )


app.jinja_env.filters["event_category_name"] = lambda u: get_event_category_name(u)
app.jinja_env.filters["loc_enum"] = lambda u: get_localized_enum_name(u)
app.jinja_env.filters["loc_scope"] = lambda s: get_localized_scope(s)
app.jinja_env.filters["env_override"] = env_override
app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
app.jinja_env.filters["is_list"] = is_list
app.jinja_env.filters["js_bool"] = js_bool
app.jinja_env.filters["any_dict_value_true"] = any_dict_value_true
app.jinja_env.filters["ensure_link_scheme"] = lambda s: ensure_link_scheme(s)
app.jinja_env.filters["place_str"] = lambda p: get_place_str(p)
app.jinja_env.filters["location_str"] = lambda location: get_location_str(location)
app.jinja_env.filters["human_file_size"] = lambda size: human_file_size(size)


def get_base_url():
    return url_for("home", _external=True).rstrip("/")


def url_for_image(image, **values):
    return url_for("image", id=image.id, hash=image.get_hash(), **values)


app.jinja_env.globals.update(
    get_base_url=get_base_url,
    url_for_image=url_for_image,
)


@app.context_processor
def get_context_processors():
    from project.access import has_access
    from project.views.utils import get_current_admin_unit

    def get_manage_menu_options(admin_unit):
        from project.access import has_access
        from project.services.event_suggestion import get_event_reviews_badge_query
        from project.services.reference import (
            get_reference_requests_incoming_badge_query,
        )
        from project.services.verification import (
            get_verification_requests_incoming_badge_query,
        )

        reviews_badge = 0
        reference_requests_incoming_badge = get_reference_requests_incoming_badge_query(
            admin_unit
        ).count()
        verification_requests_incoming_badge = (
            get_verification_requests_incoming_badge_query(admin_unit).count()
        )

        if has_access(admin_unit, "event:verify"):
            reviews_badge = get_event_reviews_badge_query(admin_unit).count()

        return {
            "reviews_badge": reviews_badge,
            "reference_requests_incoming_badge": reference_requests_incoming_badge,
            "verification_requests_incoming_badge": verification_requests_incoming_badge,
        }

    def has_tos():
        from project.services.admin import has_tos

        return has_tos()

    def get_current_user_roles():
        from flask_security import current_user

        if not current_user.is_authenticated:  # pragma: no cover
            return []

        return [r.name for r in current_user.roles]

    def get_current_user_permissions():
        from flask_security import current_user

        if not current_user.is_authenticated:  # pragma: no cover
            return []

        return sum([r.permissions for r in current_user.roles], [])

    def get_current_admin_unit_roles():
        from project.access import get_current_user_member_for_admin_unit

        current_admin_unit = get_current_admin_unit()

        if not current_admin_unit:  # pragma: no cover
            return []

        member = get_current_user_member_for_admin_unit(current_admin_unit.id)

        if not member:  # pragma: no cover
            return []

        return [r.name for r in member.roles]

    def get_current_admin_unit_permissions():
        from project.access import get_current_user_member_for_admin_unit

        current_admin_unit = get_current_admin_unit()

        if not current_admin_unit:  # pragma: no cover
            return []

        member = get_current_user_member_for_admin_unit(current_admin_unit.id)

        if not member:  # pragma: no cover
            return []

        return sum([r.permissions for r in member.roles], [])

    return dict(
        current_admin_unit=get_current_admin_unit(),
        get_current_admin_unit_roles=get_current_admin_unit_roles,
        get_current_admin_unit_permissions=get_current_admin_unit_permissions,
        get_manage_menu_options=get_manage_menu_options,
        has_access=has_access,
        has_tos=has_tos,
        get_current_user_roles=get_current_user_roles,
        get_current_user_permissions=get_current_user_permissions,
    )
