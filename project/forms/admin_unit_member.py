from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from project.forms.widgets import MultiCheckboxField


class InviteAdminUnitMemberForm(FlaskForm):
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])
    roles = MultiCheckboxField(lazy_gettext("Roles"))
    submit = SubmitField(lazy_gettext("Invite"))


class NegotiateAdminUnitMemberInvitationForm(FlaskForm):
    accept = SubmitField(lazy_gettext("Accept"))
    decline = SubmitField(lazy_gettext("Decline"))


class DeleteAdminUnitInvitationForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete invitation"))
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])


class DeleteAdminUnitMemberForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete member"))
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])


class UpdateAdminUnitMemberForm(FlaskForm):
    roles = MultiCheckboxField(lazy_gettext("Roles"))
    submit = SubmitField(lazy_gettext("Update member"))
