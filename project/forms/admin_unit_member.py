from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired

from project.forms.widgets import MultiCheckboxField


class NegotiateAdminUnitMemberInvitationForm(FlaskForm):
    accept = SubmitField(lazy_gettext("Accept"))
    decline = SubmitField(lazy_gettext("Decline"))


class DeleteAdminUnitMemberForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete member"))
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])


class UpdateAdminUnitMemberForm(FlaskForm):
    roles = MultiCheckboxField(lazy_gettext("Roles"))
    submit = SubmitField(lazy_gettext("Update member"))
