from flask_babel import lazy_gettext
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseDeleteForm
from project.views.user_blueprint.oauth2_client.forms import BaseOAuth2ClientForm


class BaseAppForm(BaseOAuth2ClientForm):
    app_permissions = MultiCheckboxField(
        lazy_gettext("Permissions"),
        validators=[DataRequired()],
        render_kw={"ri": "multicheckbox"},
    )
    homepage_url = StringField(
        lazy_gettext("Homepage URL"), validators=[Optional(), Length(max=255)]
    )
    setup_url = StringField(
        lazy_gettext("Setup URL"), validators=[Optional(), Length(max=255)]
    )
    webhook_url = StringField(
        lazy_gettext("Webhook URL"), validators=[Optional(), Length(max=255)]
    )
    webhook_secret = StringField(
        lazy_gettext("Webhook Secret"), validators=[Optional(), Length(max=255)]
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        validators=[Optional()],
    )


class CreateAppForm(BaseAppForm):
    pass


class UpdateAppForm(BaseAppForm):
    pass


class DeleteAppForm(BaseDeleteForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
