from flask_babelex import gettext, lazy_gettext
from flask_security import url_for_security
from flask_security.forms import (
    ConfirmRegisterForm,
    EqualTo,
    LoginForm,
    get_form_field_label,
)
from flask_security.utils import localize_callback
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from project.forms.common import get_accept_tos_markup
from project.views.utils import flash_message


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
        self._fields["email"].description = lazy_gettext("register_email_desc")
        self._fields["accept_tos"].label.text = get_accept_tos_markup()


class ExtendedLoginForm(LoginForm):
    def validate(self, **kwargs):
        result = super().validate(**kwargs)

        if not result and self.requires_confirmation:
            flash_message(
                gettext("login_confirmation_required"),
                url_for_security("send_confirmation"),
                localize_callback("Resend confirmation instructions"),
                "danger",
            )

        return result


class AuthorizeForm(FlaskForm):
    allow = SubmitField(lazy_gettext("Allow"))
    deny = SubmitField(lazy_gettext("Deny"))
