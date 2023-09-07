from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField, RadioField, StringField, SubmitField, TextAreaField
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


class UpdateAdminUnitForm(FlaskForm):
    incoming_reference_requests_allowed = BooleanField(
        lazy_gettext("Incoming reference requests allowed"),
        description=lazy_gettext(
            "If set, other organizations can ask this organization to reference their event."
        ),
        validators=[Optional()],
    )
    suggestions_enabled = BooleanField(
        lazy_gettext("Suggestions enabled"),
        description=lazy_gettext("If set, the organization can work with suggestions."),
        validators=[Optional()],
    )
    can_create_other = BooleanField(
        lazy_gettext("Create other organizations"),
        description=lazy_gettext(
            "If set, members of the organization can create other organizations."
        ),
        validators=[Optional()],
    )
    can_invite_other = BooleanField(
        lazy_gettext("Invite other organizations"),
        description=lazy_gettext(
            "If set, members of the organization can invite other organizations."
        ),
        validators=[Optional()],
    )
    can_verify_other = BooleanField(
        lazy_gettext("Verify other organizations"),
        description=lazy_gettext(
            "If set, members of the organization can verify other organizations."
        ),
        validators=[Optional()],
    )
    submit = SubmitField(lazy_gettext("Update organization"))


class DeleteAdminUnitForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete organization"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


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
