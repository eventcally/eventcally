from datetime import datetime, timedelta

from flask import g
from flask_login.utils import encode_cookie

from project import app


@app.after_request
def set_manage_admin_unit_cookie(response):
    manage_admin_unit_id = getattr(g, "manage_admin_unit_id", 0)
    if manage_admin_unit_id > 0:
        encoded = encode_cookie(str(manage_admin_unit_id))
        response.set_cookie(
            "manage_admin_unit_id",
            value=encoded,
            expires=datetime.utcnow() + timedelta(days=365),
        )

    return response
