import datetime

from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import current_user
from flask_security.utils import get_post_login_redirect

from project import db
from project.modular.base_views import BaseDeleteView, BaseUpdateView
from project.services.user import is_user_admin_member, set_user_accepted_tos
from project.views.user import send_user_deletion_requested_mail
from project.views.user_blueprint.user.forms import (
    AcceptTosForm,
    CancelDeletionForm,
    GeneralForm,
    NotificationForm,
    RequestDeletionForm,
)
from project.views.utils import (
    current_admin_unit,
    flash_non_match_for_deletion,
    handle_db_error,
)


class RequestDeletionView(BaseDeleteView):
    template_file_name = "delete.html"
    form_class = RequestDeletionForm

    def check_object_access(self, object):
        result = super().check_object_access(object)

        if result:  # pragma: no cover
            return result

        if object.deletion_requested_at:  # pragma: no cover
            return redirect(url_for("user.cancel_deletion"))

        if is_user_admin_member(current_user):
            flash(
                gettext(
                    "You are administrator of at least one organization. Cancel your membership to delete your account."
                ),
                "danger",
            )
            return redirect(url_for("manage_admin_units"))

    def get_title(self, **kwargs):
        return lazy_gettext("Delete account")

    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "The account is not deleted immediately. After a period of time, the account will be deleted. Until then, the deletion can be canceled."
        )

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.email.data,
            object.email,
            gettext("Entered email does not match your email"),
        )

    def delete_object_from_db(self, object):
        object.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()

    def after_commit(self, object, form):
        send_user_deletion_requested_mail(object)

    def get_redirect_url(self, **kwargs):
        return url_for("profile")

    def flask_success_text(self, form, object):
        pass


class CancelDeletionView(BaseDeleteView):
    template_file_name = "delete.html"
    form_class = CancelDeletionForm

    def check_object_access(self, object):
        result = super().check_object_access(object)

        if result:  # pragma: no cover
            return result

        if not object.deletion_requested_at:  # pragma: no cover
            return redirect(
                url_for("manage_admin_unit.request_deletion", id=current_admin_unit.id)
            )

    def get_title(self, **kwargs):
        return lazy_gettext("Cancel deletion")

    def get_instruction(self, **kwargs):
        return ""

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.email.data,
            object.email,
            gettext("Entered email does not match your email"),
        )

    def delete_object_from_db(self, object):
        object.deletion_requested_at = None
        db.session.commit()

    def get_redirect_url(self, **kwargs):
        return url_for("profile")

    def flask_success_text(self, form, object):
        pass


class BaseSettingView(BaseUpdateView):
    def get_success_text(self, object, form):
        return gettext("Settings successfully updated")

    def get_redirect_url(self, **kwargs):
        return url_for("profile")


class GeneralView(BaseSettingView):
    form_class = GeneralForm

    def get_title(self, **kwargs):
        return lazy_gettext("General")


class NotificationView(BaseSettingView):
    form_class = NotificationForm

    def get_title(self, **kwargs):
        return lazy_gettext("Notifications")


class AcceptTosView(BaseUpdateView):
    form_class = AcceptTosForm

    def get_title(self, **kwargs):
        return lazy_gettext("Confirmation required")

    def check_object_access(self, object):
        result = super().check_object_access(object)

        if result:  # pragma: no cover
            return result

        if object.tos_accepted_at:  # pragma: no cover
            return redirect(get_post_login_redirect())

    @handle_db_error
    def dispatch_validated_form(self, form, object, **kwargs):
        set_user_accepted_tos(current_user)
        db.session.commit()
        return redirect(get_post_login_redirect())
