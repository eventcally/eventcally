from project import app, babel
from flask import request

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

def print_dynamic_texts():
    gettext('Event_Art')
    gettext('Event_Book')
    gettext('Event_Movie')
    gettext('Event_Family')
    gettext('Event_Festival')
    gettext('Event_Religious')
    gettext('Event_Shopping')
    gettext('Event_Comedy')
    gettext('Event_Music')
    gettext('Event_Dance')
    gettext('Event_Nightlife')
    gettext('Event_Theater')
    gettext('Event_Dining')
    gettext('Event_Conference')
    gettext('Event_Meetup')
    gettext('Event_Fitness')
    gettext('Event_Sports')
    gettext('Event_Other')
    gettext('Typical Age range')
    gettext('Administrator')
    gettext('Event expert')
    gettext('EventReviewStatus.inbox')
    gettext('EventReviewStatus.verified')
    gettext('EventReviewStatus.rejected')