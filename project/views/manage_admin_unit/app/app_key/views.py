from io import BytesIO

from flask import abort, request, send_file, session
from flask_babel import gettext

from project.modular.base_form import BaseCreateForm
from project.modular.base_views import BaseCreateView, BaseReadView
from project.views.utils import flash_message


class CreateView(BaseCreateView):
    form_class = BaseCreateForm

    def complete_object(self, object, form):
        super().complete_object(object, form)

        private_pem = object.generate_key()
        session["private_pem"] = private_pem.decode("utf-8")

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
