from flask import redirect
from flask_babel import lazy_gettext

from project.modular.base_views import BaseUpdateView
from project.views.user_blueprint.oauth2_token.forms import RevokeOAuth2TokenForm


class RevokeView(BaseUpdateView):
    form_class = RevokeOAuth2TokenForm
    template_file_name = "update.html"

    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.is_revoked() > 0:
            return redirect(self.get_redirect_url())

        return None

    def complete_object(self, object):
        super().complete_object(object)
        object.revoke_token()

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Revoke %(model_display_name)s",
            model_display_name=self.model.get_display_name(),
        )

    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "Do you want to revoke '%(object_title)s'?",
            object_title=str(kwargs["object"]),
        )

    def get_success_text(self):
        return lazy_gettext(
            "%(model_display_name)s successfully revoked",
            model_display_name=self.model.get_display_name(),
        )
