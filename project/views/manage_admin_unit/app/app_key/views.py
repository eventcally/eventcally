from io import BytesIO

from flask import abort, g, redirect, request, send_file, session
from flask_babel import gettext

from project.application.commands import CreateAppKeyCommand, DeleteAppKeyCommand
from project.modular.base_form import BaseCreateForm
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseReadView
from project.views.utils import current_admin_unit, flash_message, handle_base_error


class CreateView(BaseCreateView):
    form_class = BaseCreateForm

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = CreateAppKeyCommand(
            actor=self.app_context_provider.get_current_actor(),
            admin_unit_id=current_admin_unit.id,
            app_id=g.current_app.id,
        )
        cmd_result = self.message_bus.handle_command(cmd)
        session["private_pem"] = cmd_result.private_pem
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))

    def flash_success_message(self, object, form):
        super().flash_success_message(object, form)

        text = gettext(
            "Please download the private key. It will only be available once."
        )
        flash_message(
            text,
            self.handler.get_read_url(object, download_pem=1),
            gettext("Download"),
            "warning",
        )


class ReadView(BaseReadView):
    def render_template(self, **kwargs):
        if "download_pem" in request.args:
            private_pem = session.pop("private_pem", None)

            if not private_pem:  # pragma: no cover
                abort(404)

            return send_file(
                BytesIO(private_pem.encode("utf-8")),
                mimetype="application/x-pem-file",
                as_attachment=True,
                download_name="private_key.pem",
            )

        return super().render_template(**kwargs)


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteAppKeyCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
