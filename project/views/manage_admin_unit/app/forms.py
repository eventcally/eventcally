from flask_babel import lazy_gettext
from wtforms import FormField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from project.domain.commands.create_app_command import CreateAppCommand
from project.domain.commands.update_app_command import UpdateAppCommand
from project.forms.common import WebhookForm
from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseDeleteForm
from project.utils import split_by_crlf
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
    description = TextAreaField(
        lazy_gettext("Description"),
        validators=[Optional()],
    )
    webhook = FormField(WebhookForm, lazy_gettext("Webhook"))


class CreateAppForm(BaseAppForm):
    def create_create_command(self, admin_unit_id: int) -> CreateAppCommand:
        return CreateAppCommand.model_construct(
            admin_unit_id=admin_unit_id,
            name=self.client_name.data,
            app_permissions=self.app_permissions.data,
            redirect_uris=split_by_crlf(self.redirect_uris.data),
            scope=" ".join(self.scope.data),
            description=self.description.data,
            homepage_url=self.homepage_url.data,
            setup_url=self.setup_url.data,
            webhook=self.webhook.form.create_create_command(),
        )


class UpdateAppForm(BaseAppForm):
    def create_update_command(self, app_id: int) -> UpdateAppCommand:
        return UpdateAppCommand.model_construct(
            id=app_id,
            name=self.client_name.data,
            app_permissions=self.app_permissions.data,
            redirect_uris=split_by_crlf(self.redirect_uris.data),
            scope=" ".join(self.scope.data),
            description=self.description.data,
            homepage_url=self.homepage_url.data,
            setup_url=self.setup_url.data,
            webhook=self.webhook.form.create_update_command(),
        )


class DeleteAppForm(BaseDeleteForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
