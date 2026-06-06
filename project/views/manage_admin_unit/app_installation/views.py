from flask import flash, redirect
from flask_babel import gettext, lazy_gettext

from project.application.commands import UninstallAppCommand
from project.models.oauth import OAuth2Client
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.permissions import get_organization_permission_infos
from project.views.manage_admin_unit.app_installation.displays import (
    AcceptPermissionsDisplay,
    InstallDisplay,
)
from project.views.manage_admin_unit.app_installation.forms import (
    AcceptPermissionsForm,
    InstallAppForm,
)
from project.views.utils import current_admin_unit, flash_message, handle_base_error


class InstallView(BaseCreateView):
    form_class = InstallAppForm
    template_file_name = "install.html"
    display_class = InstallDisplay

    def dispatch_request(self, **kwargs):
        self.oauth2_client = OAuth2Client.query.get_or_404(kwargs.get("app_id"))
        return super().dispatch_request(**kwargs)

    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "Do you want to install '%(app_name)s'?",
            app_name=self.oauth2_client.client_name,
        )

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.permissions.choices = [
            (i.permission, i.label)
            for i in get_organization_permission_infos(
                self.oauth2_client.app_permissions
            )
        ]
        form.permissions.data = [c[0] for c in form.permissions.choices]

        return form

    def render_template(self, **kwargs):
        kwargs.setdefault("oauth2_client", self.oauth2_client)
        return super().render_template(**kwargs)

    @handle_base_error
    def dispatch_validated_form(self, form: InstallAppForm, object, **kwargs):
        cmd = form.create_create_command(
            admin_unit_id=current_admin_unit.id,
            app_id=self.oauth2_client.id,
        )
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))

    def flash_success_message(self, object, form):
        text = gettext("App successfully installed")

        if self.oauth2_client.setup_url:  # pragma: no cover
            flash_message(
                text,
                self.oauth2_client.setup_url,
                gettext("Setup"),
                "success",
            )
        else:
            flash(text, "success")


class AcceptPermissionsView(BaseUpdateView):
    form_class = AcceptPermissionsForm
    display_class = AcceptPermissionsDisplay

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)
        oauth2_client = kwargs.get("obj").oauth2_client

        form.permissions.choices = [
            (i.permission, i.label)
            for i in get_organization_permission_infos(oauth2_client.app_permissions)
        ]
        form.permissions.data = [c[0] for c in form.permissions.choices]

        return form

    @handle_base_error
    def dispatch_validated_form(self, form: AcceptPermissionsForm, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = UninstallAppCommand.model_construct(id=object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
