import json

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField, RadioField, SubmitField, TextAreaField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Optional

from project.forms.widgets import MultiCheckboxField


class AdminSettingsForm(FlaskForm):
    tos = TextAreaField(lazy_gettext("Terms of service"), validators=[Optional()])
    legal_notice = TextAreaField(lazy_gettext("Legal notice"), validators=[Optional()])
    contact = TextAreaField(lazy_gettext("Contact"), validators=[Optional()])
    privacy = TextAreaField(lazy_gettext("Privacy"), validators=[Optional()])
    start_page = TextAreaField(lazy_gettext("Start page"), validators=[Optional()])
    announcement = TextAreaField(lazy_gettext("Announcement"), validators=[Optional()])

    submit = SubmitField(lazy_gettext("Save"))


class AdminPlanningForm(FlaskForm):
    planning_external_calendars = TextAreaField(
        lazy_gettext("External calendars"), validators=[Optional()]
    )

    submit = SubmitField(lazy_gettext("Save"))

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if self.planning_external_calendars.data:
            try:
                json_object = json.loads(self.planning_external_calendars.data)
                self.planning_external_calendars.data = json.dumps(
                    json_object, indent=2
                )
            except Exception as e:  # pragma: no cover
                msg = str(e)
                self.planning_external_calendars.errors.append(msg)
                result = False

        return result


class ResetTosAceptedForm(FlaskForm):
    reset_for_users = BooleanField(
        lazy_gettext("Reset for all users"), validators=[DataRequired()]
    )
    submit = SubmitField(lazy_gettext("Reset"))


class UpdateUserForm(FlaskForm):
    roles = MultiCheckboxField(lazy_gettext("Roles"))
    submit = SubmitField(lazy_gettext("Update user"))


class DeleteUserForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete user"))
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])


class AdminTestEmailForm(FlaskForm):
    recipient = EmailField(lazy_gettext("Recipient"), validators=[DataRequired()])

    submit = SubmitField(lazy_gettext("Send test mail synchronously"))


class AdminNewsletterForm(FlaskForm):
    recipient_choice = RadioField(
        lazy_gettext("Recipient"),
        choices=[
            (1, lazy_gettext("Test recipient")),
            (2, lazy_gettext("All users with enabled newsletter setting")),
        ],
        default=1,
        coerce=int,
    )
    test_recipient = EmailField(lazy_gettext("Test recipient"), validators=[Optional()])
    message = TextAreaField(lazy_gettext("Message"), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext("Send newsletter"))
