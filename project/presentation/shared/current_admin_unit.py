from flask import g, request
from flask_login.utils import decode_cookie
from flask_security import current_user
from werkzeug.local import LocalProxy

from project.presentation.shared.access import (
    get_admin_unit_for_manage,
    get_admin_units_for_manage,
)

current_admin_unit = LocalProxy(lambda: get_current_admin_unit(False, False, False))


def set_current_admin_unit(admin_unit):
    if admin_unit:
        setattr(g, "manage_admin_unit", admin_unit)


def get_current_admin_unit(fallback=True, use_cookies=True, use_headers=False):
    admin_unit = getattr(g, "manage_admin_unit", None)

    if admin_unit:
        return admin_unit

    if current_user and current_user.is_authenticated:
        if use_cookies:
            admin_unit = get_current_admin_unit_from_cookies()

        if not admin_unit and use_headers:
            admin_unit = get_current_admin_unit_from_headers()

        if not admin_unit and fallback:
            admin_units = get_admin_units_for_manage()

            if len(admin_units) > 0:
                admin_unit = admin_units[0]

    if admin_unit:
        set_current_admin_unit(admin_unit)

    return admin_unit


def get_current_admin_unit_for_api():
    return get_current_admin_unit(fallback=False, use_cookies=False, use_headers=True)


def get_current_admin_unit_from_cookies():
    try:
        if request and request.cookies and "manage_admin_unit_id" in request.cookies:
            encoded = request.cookies.get("manage_admin_unit_id")
            manage_admin_unit_id = int(decode_cookie(encoded))
            return get_admin_unit_for_manage(manage_admin_unit_id)
    except Exception:
        pass

    return None


def get_current_admin_unit_from_headers():
    try:
        if request and request.headers and "X-OrganizationId" in request.headers:
            manage_admin_unit_id_str = request.headers["X-OrganizationId"]
            manage_admin_unit_id = int(manage_admin_unit_id_str)
            return get_admin_unit_for_manage(manage_admin_unit_id)
    except Exception:
        pass

    return None
