import os
from urllib.parse import quote_plus

from flask import current_app, url_for
from markupsafe import Markup

from project.application.queries import (
    GetCurrentMemberGrantsQuery,
    GetManageMenuOptionsQuery,
    GetSiteNoticesQuery,
)
from project.presentation.shared.urls import url_for_image
from project.presentation.web.vite import vite_entry
from project.shared.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_location_str,
    get_place_str,
)


def _query_bus():
    return current_app.container.cqrs.query_bus()


def env_override(value, key):
    return os.getenv(key, value)


def is_list(value):  # pragma: no cover
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
        else (
            human_file_size(bytes >> 10, units[1:]) if units[1:] else f"{bytes >> 10}ZB"
        )
    )


def get_base_url():
    return url_for("main.home", _external=True).rstrip("/")


def get_main_menu():
    """The main navbar entries, shared by the Bootstrap 4 and 5 frames."""
    from flask_babel import gettext
    from flask_security import current_user

    main = [
        {"label": gettext("Events"), "url": url_for("main.event_dates")},
        {"label": gettext("Organizations"), "url": url_for("main.organizations")},
        {"label": gettext("Planning"), "url": url_for("main.planning")},
    ]
    docs = None
    if current_app.config.get("DOCS_URL"):
        docs = {"label": gettext("Docs"), "url": current_app.config["DOCS_URL"]}

    authenticated = current_user.is_authenticated
    user_items = []
    if authenticated:
        user_items = [
            {
                "label": gettext("Organizations"),
                "url": url_for("main.manage_admin_units"),
            },
            {"label": gettext("Profile"), "url": url_for("main.profile")},
        ]
        if current_user.has_role("admin"):
            user_items.append(
                {"label": gettext("Admin"), "url": url_for("admin.shell", path="")}
            )
        user_items.append(
            {"label": gettext("Logout"), "url": url_for("security.logout")}
        )

    return {
        "main": main,
        "docs": docs,
        "user_email": current_user.email if authenticated else None,
        "user_items": user_items,
    }


def init_jinja_filters(app):
    """Initialize Jinja filters and globals with the Flask app instance.

    This function registers custom Jinja filters, globals, and context processors.
    Must be called from create_app() to support the application factory pattern.

    Args:
        app: Flask application instance
    """
    # Register filters
    app.jinja_env.filters["event_category_name"] = lambda u: get_event_category_name(u)
    app.jinja_env.filters["loc_enum"] = lambda u: get_localized_enum_name(u)
    app.jinja_env.filters["env_override"] = env_override
    app.jinja_env.filters["quote_plus"] = lambda u: quote_plus(u)
    app.jinja_env.filters["is_list"] = is_list
    app.jinja_env.filters["js_bool"] = js_bool
    app.jinja_env.filters["any_dict_value_true"] = any_dict_value_true
    app.jinja_env.filters["ensure_link_scheme"] = lambda s: ensure_link_scheme(s)
    app.jinja_env.filters["place_str"] = lambda p: get_place_str(p)
    app.jinja_env.filters["location_str"] = lambda location: get_location_str(location)
    app.jinja_env.filters["human_file_size"] = lambda size: human_file_size(size)

    # Register globals
    app.jinja_env.globals.update(
        get_base_url=get_base_url,
        url_for_image=url_for_image,
        vite_entry=vite_entry,
    )

    # Register context processor
    @app.context_processor
    def get_context_processors():
        from project.presentation.shared.access import has_access
        from project.presentation.shared.current_admin_unit import (
            get_current_admin_unit,
        )

        def get_manage_menu_options(admin_unit):
            return (
                _query_bus()
                .handle(GetManageMenuOptionsQuery(admin_unit_id=admin_unit.id))
                .model_dump()
            )

        def has_tos():
            return _query_bus().handle(GetSiteNoticesQuery()).has_tos

        def get_announcement():
            announcement = _query_bus().handle(GetSiteNoticesQuery()).announcement
            return Markup(announcement) if announcement else None

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
            current_admin_unit = get_current_admin_unit()

            if not current_admin_unit:  # pragma: no cover
                return []

            return (
                _query_bus()
                .handle(
                    GetCurrentMemberGrantsQuery(admin_unit_id=current_admin_unit.id)
                )
                .roles
            )

        def get_current_admin_unit_permissions():
            current_admin_unit = get_current_admin_unit()

            if not current_admin_unit:  # pragma: no cover
                return []

            return (
                _query_bus()
                .handle(
                    GetCurrentMemberGrantsQuery(admin_unit_id=current_admin_unit.id)
                )
                .permissions
            )

        return dict(
            get_main_menu=get_main_menu,
            current_admin_unit=get_current_admin_unit(),
            get_current_admin_unit_roles=get_current_admin_unit_roles,
            get_current_admin_unit_permissions=get_current_admin_unit_permissions,
            get_manage_menu_options=get_manage_menu_options,
            has_access=has_access,
            has_tos=has_tos,
            get_announcement=get_announcement,
            get_current_user_roles=get_current_user_roles,
            get_current_user_permissions=get_current_user_permissions,
        )
