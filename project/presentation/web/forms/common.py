from flask import current_app, url_for
from flask_babel import lazy_gettext
from markupsafe import Markup

from project.application.queries import GetSiteNoticesQuery
from project.presentation.shared.event_rating import event_rating_choices  # noqa: F401


def get_accept_tos_markup():
    tos_open = '<a href="%s">' % url_for("main.tos")
    tos_close = "</a>"

    privacy_open = '<a href="%s">' % url_for("main.privacy")
    privacy_close = "</a>"

    if current_app.container.cqrs.query_bus().handle(GetSiteNoticesQuery()).has_tos:
        return Markup(
            lazy_gettext(
                "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.",
                tos_open=tos_open,
                tos_close=tos_close,
                privacy_open=privacy_open,
                privacy_close=privacy_close,
            )
        )

    return Markup(
        lazy_gettext(
            "I read and accept %(privacy_open)sPrivacy%(privacy_close)s.",
            tos_open=tos_open,
            tos_close=tos_close,
            privacy_open=privacy_open,
            privacy_close=privacy_close,
        )
    )


weekday_choices = [
    (1, lazy_gettext("Monday")),
    (2, lazy_gettext("Tueday")),
    (3, lazy_gettext("Wednesday")),
    (4, lazy_gettext("Thursday")),
    (5, lazy_gettext("Friday")),
    (6, lazy_gettext("Saturday")),
    (0, lazy_gettext("Sunday")),
]
