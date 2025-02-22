import datetime

from flask import redirect, request, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import current_user

from project import db
from project.modular.base_views import BaseDeleteView, BaseUpdateView
from project.utils import widget_default_background_color, widget_default_primary_color
from project.views.admin_unit import send_admin_unit_deletion_requested_mails
from project.views.manage_admin_unit.admin_unit.forms import (
    CancelDeletionForm,
    RequestDeletionForm,
    UpdateForm,
    UpdateWidgetForm,
)
from project.views.utils import (
    current_admin_unit,
    flash_non_match_for_deletion,
    manage_permission_required,
)


class UpdateView(BaseUpdateView):
    decorators = [manage_permission_required("admin_unit:update")]
    form_class = UpdateForm

    def get_title(self, **kwargs):
        return lazy_gettext("Settings")

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not current_admin_unit.can_verify_other:
            del form.verfication_requests

        return form

    def get_redirect_url(self, **kwargs):
        return url_for(request.endpoint)


class UpdateWidgetView(BaseUpdateView):
    template_file_name = "widgets.html"
    decorators = [manage_permission_required("admin_unit:update")]
    form_class = UpdateWidgetForm

    def get_title(self, **kwargs):
        return lazy_gettext("Widgets")

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not form.widget_background_color.data:
            form.widget_background_color.data = widget_default_background_color

        if not form.widget_primary_color.data:
            form.widget_primary_color.data = widget_default_primary_color

        if not form.widget_link_color.data:
            form.widget_link_color.data = widget_default_primary_color

        return form

    def complete_object(self, object, form):
        super().complete_object(object, form)

        if form.widget_background_color.data == widget_default_background_color:
            object.widget_background_color = None

        if form.widget_primary_color.data == widget_default_primary_color:
            object.widget_primary_color = None

        if form.widget_link_color.data == widget_default_primary_color:
            object.widget_link_color = None

    def get_success_text(self, object, form):
        return gettext("Settings successfully updated")

    def get_redirect_url(self, **kwargs):
        return url_for(request.endpoint)


class RequestDeletionView(BaseDeleteView):
    template_file_name = "delete.html"
    decorators = [manage_permission_required("admin_unit:update")]
    form_class = RequestDeletionForm

    def check_object_access(self, object):
        result = super().check_object_access(object)

        if result:  # pragma: no cover
            return result

        if object.deletion_requested_at:  # pragma: no cover
            return redirect(url_for("manage_admin_unit.cancel_deletion", id=object.id))

    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "The organization is not deleted immediately. After a period of time, the organization will be deleted. Until then, the deletion can be canceled."
        )

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.name,
            gettext("Entered name does not match organization name"),
        )

    def delete_object_from_db(self, object):
        object.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        object.deletion_requested_by_id = current_user.id
        db.session.commit()

    def after_commit(self, object, form):
        send_admin_unit_deletion_requested_mails(object)

    def get_redirect_url(self, **kwargs):
        return url_for("manage_admin_unit", id=current_admin_unit.id)

    def flask_success_text(self, form, object):
        pass


class CancelDeletionView(BaseDeleteView):
    template_file_name = "delete.html"
    decorators = [manage_permission_required("admin_unit:update")]
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
            form.name.data,
            object.name,
            gettext("Entered name does not match organization name"),
        )

    def delete_object_from_db(self, object):
        object.deletion_requested_at = None
        object.deletion_requested_by_id = None
        db.session.commit()

    def get_redirect_url(self, **kwargs):
        return url_for("manage_admin_unit", id=current_admin_unit.id)

    def flask_success_text(self, form, object):
        pass
