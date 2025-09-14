from flask import request
from flask_babel import Locale, gettext
from flask_security import current_user

from project import app


def get_locale():
    try:
        if (
            current_user
            and current_user.is_authenticated
            and current_user.locale
            and Locale.parse(current_user.locale)
        ):
            return current_user.locale
    except Exception:  # pragma: no cover
        pass

    if not request:
        return app.config["BABEL_DEFAULT_LOCALE"]

    return get_locale_from_request()


def get_locale_from_request():
    if not request:  # pragma: no cover
        return None

    return request.accept_languages.best_match(
        app.config["LANGUAGES"], app.config["BABEL_DEFAULT_LOCALE"]
    )


def print_dynamic_texts():
    gettext("Event_Art")
    gettext("Event_Book")
    gettext("Event_Movie")
    gettext("Event_Family")
    gettext("Event_Festival")
    gettext("Event_Religious")
    gettext("Event_Shopping")
    gettext("Event_Comedy")
    gettext("Event_Music")
    gettext("Event_Dance")
    gettext("Event_Nightlife")
    gettext("Event_Theater")
    gettext("Event_Dining")
    gettext("Event_Conference")
    gettext("Event_Meetup")
    gettext("Event_Fitness")
    gettext("Event_Sports")
    gettext("Event_Other")
    gettext("Event_Exhibition")
    gettext("Event_Culture")
    gettext("Event_Tour")
    gettext("Event_OpenAir")
    gettext("Event_Stage")
    gettext("Event_Lecture")
    gettext("Typical Age range")
    gettext("Administrator")
    gettext("Event expert")
    gettext("EventReviewStatus.inbox")
    gettext("EventReviewStatus.verified")
    gettext("EventReviewStatus.rejected")
    gettext("Scope_openid")
    gettext("Scope_profile")
    gettext("There must be no self-reference.")
