from flask_security.forms import RegisterForm
from wtforms import BooleanField
from wtforms.validators import DataRequired
from project.forms.common import get_accept_tos_markup


class ExtendedRegisterForm(RegisterForm):
    accept_tos = BooleanField(validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(ExtendedRegisterForm, self).__init__(*args, **kwargs)
        self._fields["accept_tos"].label.text = get_accept_tos_markup()
