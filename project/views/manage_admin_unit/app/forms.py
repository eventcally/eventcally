from flask_babel import lazy_gettext
from wtforms import StringField
from wtforms.validators import DataRequired

from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseDeleteForm
from project.views.user_blueprint.oauth2_client.forms import BaseOAuth2ClientForm


class BaseAppForm(BaseOAuth2ClientForm):
    app_permissions = MultiCheckboxField(
        lazy_gettext("Permissions"),
        validators=[DataRequired()],
        render_kw={"ri": "multicheckbox"},
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
