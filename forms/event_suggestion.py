from flask import request
from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import FieldList, RadioField, DateTimeField, StringField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, FormField
from wtforms.fields.html5 import DateTimeLocalField, EmailField, TelField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
from models import EventSuggestion, EventPlace, EventTargetGroupOrigin, EventAttendanceMode, EventStatus, Location, EventOrganizer, EventRejectionReason, EventReviewStatus, Image
from .common import event_rating_choices, BaseImageForm
from .widgets import CustomDateTimeField, CustomDateField, TagSelectField
from .common import event_rating_choices

class CreateEventSuggestionForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()], description=lazy_gettext('Gib einen kurzen, aussagekräftigen Namen für die Veranstaltung ein.'))
    start = CustomDateTimeField(lazy_gettext('Start'), validators=[DataRequired()], description=lazy_gettext('Gib an, wann die Veranstaltung stattfindet.'))
    description = TextAreaField(lazy_gettext('Description'), validators=[Optional()], description=lazy_gettext('Füge der Veranstaltung eine optionale Beschreibung hinzu.'))
    external_link = StringField(lazy_gettext('Link URL'), validators=[Optional()], description=lazy_gettext('Füge einen optionalen Link hinzu. Das kann die Prüfung erleichtern.'))

    contact_name = StringField(lazy_gettext('Name'), validators=[DataRequired()], description=lazy_gettext('Bitte gib deinen Namen für etwaige Rückfragen an.'))
    contact_phone = TelField(lazy_gettext('Phone'), validators=[Optional()], description=lazy_gettext('Bitte gib deine Telefonnummer oder deine Email-Adresse für etwaige Rückfragen an.'))
    contact_email = EmailField(lazy_gettext('Email'), validators=[Optional()], description=lazy_gettext('Bitte gib deine Email-Adresse oder deine Telefonnummer für etwaige Rückfragen an.'))
    contact_email_notice = BooleanField(lazy_gettext('Ich möchte per Email benachrichtigt werden nach der Prüfung'), validators=[Optional()])

    event_place_id = TagSelectField(lazy_gettext('Place') + ' *', validators=[Optional()], description=lazy_gettext('Wähle aus, wo die Veranstaltung stattfindet. Ist der Veranstaltungsort noch nicht in der Liste, trage ihn einfach ein.'))
    organizer_id = TagSelectField(lazy_gettext('Organizer') + ' *', validators=[Optional()], description=lazy_gettext('Wähle den Veranstalter aus. Ist der Veranstaltungsort noch nicht in der Liste, trage ihn einfach ein.'))
    photo = FormField(BaseImageForm, lazy_gettext('Photo'), default=lambda: Image(), description=lazy_gettext('Wir empfehlen dir, ein Foto für die Veranstaltung hochzuladen. Es macht schon deutlich mehr her, aber es geht natürlich auch ohne.'))
    accept_tos = BooleanField(lazy_gettext('Ich bestätige dass ich alle Informationen (Text, Bild, etc.), die ich in das System hochlade, hinsichtlich ihrer Nutzungsrechte abgeklärt habe und erkläre, dass diese weitergegeben werden dürfen.'), validators=[DataRequired()])

    submit = SubmitField(lazy_gettext("Create event suggestion"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'photo' and not obj.photo:
                obj.photo = Image()
            if name == 'event_place_id' and isinstance(self.event_place_id.data, str):
                obj.event_place_text = self.event_place_id.data
                obj.event_place_id = None
            elif name == 'organizer_id' and isinstance(self.organizer_id.data, str):
                obj.organizer_text = self.organizer_id.data
                obj.organizer_id = None
            else:
                field.populate_obj(obj, name)

class RejectEventSuggestionForm(FlaskForm):
    rejection_resaon = SelectField(lazy_gettext('Rejection reason'), coerce=int, choices=[
        (0, ''),
        (int(EventRejectionReason.duplicate), lazy_gettext('EventRejectionReason.duplicate')),
        (int(EventRejectionReason.untrustworthy), lazy_gettext('EventRejectionReason.untrustworthy')),
        (int(EventRejectionReason.illegal), lazy_gettext('EventRejectionReason.illegal'))])

    submit = SubmitField(lazy_gettext("Reject event suggestion"))
