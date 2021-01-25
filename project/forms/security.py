from flask_security.forms import RegisterForm, EqualTo, get_form_field_label
from wtforms import BooleanField, PasswordField
from wtforms.validators import DataRequired
from project.forms.common import get_accept_tos_markup


class ExtendedRegisterForm(RegisterForm):
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
        super(ExtendedRegisterForm, self).__init__(*args, **kwargs)
        self._fields["accept_tos"].label.text = get_accept_tos_markup()
