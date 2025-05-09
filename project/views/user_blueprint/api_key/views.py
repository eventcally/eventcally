from flask import flash
from flask_babel import lazy_gettext

from project.modular.base_views import BaseCreateView


class CreateView(BaseCreateView):
    def complete_object(self, object, form):
        super().complete_object(object, form)
        self.transient_key = object.generate_key()

    def flash_success_message(self, object, form):
        super().flash_success_message(object, form)

        text = lazy_gettext(
            "Please note the key: %(key)s. It will only be displayed once.",
            key=self.transient_key,
        )
        flash(text, "warning")
