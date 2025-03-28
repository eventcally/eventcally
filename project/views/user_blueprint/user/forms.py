from flask_babel import lazy_gettext
from wtforms import BooleanField, EmailField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

from project.forms.common import get_accept_tos_markup
from project.modular.base_form import BaseForm


class RequestDeletionForm(BaseForm):
    email = EmailField(lazy_gettext("Email"), validators=[DataRequired()])
    submit = SubmitField(lazy_gettext("Request deletion"))


class CancelDeletionForm(RequestDeletionForm):
    submit = SubmitField(lazy_gettext("Cancel deletion"))


class GeneralForm(BaseForm):
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


class NotificationForm(BaseForm):
    newsletter_enabled = BooleanField(
        lazy_gettext("Newsletter"),
        description=lazy_gettext("Information about new features and improvements."),
        validators=[Optional()],
        render_kw={
            "ri": "switch",
        },
    )
    submit = SubmitField(lazy_gettext("Save"))


class AcceptTosForm(BaseForm):
    accept_tos = BooleanField(validators=[DataRequired()], render_kw={"ri": "checkbox"})
    submit = SubmitField(lazy_gettext("Confirm"))

    def __init__(self, **kwargs):
        super(AcceptTosForm, self).__init__(**kwargs)
        self._fields["accept_tos"].label.text = get_accept_tos_markup()
