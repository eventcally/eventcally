from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField
from wtforms.validators import Optional


class NotificationForm(FlaskForm):
    newsletter_enabled = BooleanField(
        lazy_gettext("Newsletter"),
        description=lazy_gettext("Information about new features and improvements."),
        validators=[Optional()],
    )
    submit = SubmitField(lazy_gettext("Save"))
