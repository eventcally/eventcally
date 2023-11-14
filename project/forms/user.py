from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional


class GeneralForm(FlaskForm):
    locale = SelectField(
        lazy_gettext("Language"),
        choices=[
            ("None", lazy_gettext("Default")),
            ("de", "Deutsch"),
            ("en", "English"),
        ],
        default="None",
        validators=[Optional()],
    )
    submit = SubmitField(lazy_gettext("Save"))

    def populate_obj(self, obj):
        super().populate_obj(obj)
        if obj.locale == "None":
            obj.locale = None


class NotificationForm(FlaskForm):
    newsletter_enabled = BooleanField(
        lazy_gettext("Newsletter"),
        description=lazy_gettext("Information about new features and improvements."),
        validators=[Optional()],
    )
    submit = SubmitField(lazy_gettext("Save"))


class RequestUserDeletionForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Request deletion"))
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])


class CancelUserDeletionForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Cancel deletion"))
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])
