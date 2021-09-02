from flask import request
from flask_babelex import gettext

from project import app, babel


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config["LANGUAGES"])


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
    gettext("Scope_organizer:write")
    gettext("Scope_place:write")
    gettext("Scope_event:write")
    gettext("Scope_organization:read")
    gettext("Scope_organization:write")
    gettext("There must be no self-reference.")
