from flask_babelex import lazy_gettext
from flask_security.forms import ConfirmRegisterForm, EqualTo, get_form_field_label
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from project.forms.common import get_accept_tos_markup


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    password = PasswordField(
        get_form_field_label("password"), validators=[DataRequired()]
    )
    password_confirm = PasswordField(
        get_form_field_label("retype_password"),
        validators=[
            EqualTo("password", message="RETYPE_PASSWORD_MISMATCH"),
            DataRequired(),
        ],
    )
    accept_tos = BooleanField(validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(ExtendedConfirmRegisterForm, self).__init__(*args, **kwargs)
        self._fields["accept_tos"].label.text = get_accept_tos_markup()


class AuthorizeForm(FlaskForm):
    allow = SubmitField(lazy_gettext("Allow"))
    deny = SubmitField(lazy_gettext("Deny"))
