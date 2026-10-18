from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SubmitField


class CreateAdminUnitVerificationRequestForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Request verification"))
