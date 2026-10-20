from flask import url_for
from flask_babel import get_locale
from flask_security import current_user
from flask_wtf.csrf import generate_csrf


def build_boot_data(base: str) -> dict:
    """The JSON the SPA shell hands to the Vue app (`#boot`)."""
    return {
        "base": base,
        "bffBase": "/bff",
        "locale": str(get_locale() or "en").split("_")[0],
        "csrfToken": generate_csrf(),
        "user": {
            "email": current_user.email,
            "roles": [r.name for r in current_user.roles],
        },
        "loginUrl": url_for("security.login"),
    }
