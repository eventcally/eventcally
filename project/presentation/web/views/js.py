from dependency_injector.wiring import Provide, inject
from flask import request
from flask.json import jsonify
from flask_babel import gettext
from flask_cors import cross_origin
from flask_security import url_for_security
from flask_security.utils import localize_callback

from project.application.queries import GetCustomWidgetQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.infrastructure.extensions import csrf
from project.infrastructure.user_datastore import find_user_by_email
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.views.main_blueprint import main_bp
from project.shared.dateutils import gmt_tz


@main_bp.route("/js/check/register/email", methods=["POST"])
def js_check_register_email():
    csrf.protect()

    email = request.form["email"]
    user = find_user_by_email(email)

    if not user:
        return jsonify(True)

    msg = gettext("An account already exists with this email.")
    url = url_for_security("forgot_password")
    link_text = localize_callback("Forgot password?")
    link = ' &ndash; <a href="%s">%s</a>' % (url, link_text)
    error = msg + link
    return jsonify(error)


def _gmt_iso(value):
    if value is None:
        return None

    if value.tzinfo:
        value = value.astimezone(gmt_tz)
    else:
        value = value.replace(tzinfo=gmt_tz)

    return value.isoformat()


def _custom_widget_json(widget) -> dict:
    """The payload `widget-loader.js` on customer sites reads; keep the keys."""
    return {
        "id": widget.id,
        "widget_type": widget.widget_type,
        "name": widget.name,
        "settings": widget.settings,
        "created_at": _gmt_iso(widget.created_at),
        "updated_at": _gmt_iso(widget.updated_at),
        "organization": {
            "id": widget.admin_unit.id,
            "name": widget.admin_unit.name,
        },
    }


@main_bp.route("/js/wlcw/<int:id>")
@cross_origin()
@inject
def js_widget_loader_custom_widget(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    widget = result_or_404(query_bus.handle(GetCustomWidgetQuery(id=id)))
    return _custom_widget_json(widget)
