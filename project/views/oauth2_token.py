from flask import redirect, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import auth_required, current_user

from project import app
from project.access import owner_access_or_401
from project.forms.oauth2_token import RevokeOAuth2TokenForm
from project.models import OAuth2Token
from project.views.base_display import BaseDisplay
from project.views.base_props import DateTimeProp, MethodProp, StringProp
from project.views.base_view_handler import BaseViewHandler
from project.views.base_views import BaseUpdateView


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


class ListDisplay(BaseDisplay):
    id = StringProp(lazy_gettext("ID"))
    client_name = StringProp(lazy_gettext("Application"))
    scope = StringProp(lazy_gettext("Scopes"))
    issued_at_datetime = DateTimeProp(lazy_gettext("Issued"))
    expires_at_datetime = DateTimeProp(lazy_gettext("Expires"))
    status = MethodProp("get_status_display_value", lazy_gettext("Status"))

    def get_status_display_value(self, object):
        if object.is_expired():  # pragma: no cover
            return gettext("Expired")

        if object.is_revoked():  # pragma: no cover
            return gettext("Revoked")

        return None


class OAuth2TokenViewHandler(BaseViewHandler):
    decorators = [auth_required()]
    model = OAuth2Token
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay

    def add_views(self, app, url_prefix, endpoint_prefix):
        super().add_views(app, url_prefix, endpoint_prefix)

        self._add_view(
            "revoke",
            f"/{url_prefix}/<int:id>/revoke",
            RevokeView,
            f"{endpoint_prefix}_revoke",
            app,
        )

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()
        result.append(self._create_breadcrumb(url_for("profile"), gettext("Profile")))
        return result

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        if not object.is_revoked():
            revoke_action = self._create_action(
                self.get_endpoint_url("revoke", id=object.id), gettext("Revoke")
            )
            if revoke_action:
                result.append(revoke_action)

        return result

    def check_object_access(self, object):
        return owner_access_or_401(object.user_id)

    def apply_base_filter(self, query, **kwargs):
        return query.filter(OAuth2Token.user_id == current_user.id)

    def apply_objects_query_order(self, query, **kwargs):
        return query.order_by(OAuth2Token.issued_at.desc())


handler = OAuth2TokenViewHandler()
handler.init_app(app)
