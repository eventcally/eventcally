from flask_wtf import FlaskForm
from flask_babelex import lazy_gettext
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional


class AdminSettingsForm(FlaskForm):
    tos = TextAreaField(lazy_gettext("Terms of service"), validators=[Optional()])
    legal_notice = TextAreaField(lazy_gettext("Legal notice"), validators=[Optional()])
    contact = TextAreaField(lazy_gettext("Contact"), validators=[Optional()])
    privacy = TextAreaField(lazy_gettext("Privacy"), validators=[Optional()])

    submit = SubmitField(lazy_gettext("Save"))
