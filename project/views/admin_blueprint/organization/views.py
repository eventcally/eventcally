from flask import redirect
from flask_babel import gettext

from project.modular.base_views import BaseDeleteView, BaseUpdateView
from project.views.admin_blueprint.organization.forms import DeleteForm, UpdateForm
from project.views.utils import flash_non_match_for_deletion, handle_base_error


class UpdateView(BaseUpdateView):
    form_class = UpdateForm

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    form_class = DeleteForm

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.name,
            gettext("Entered name does not match organization name"),
        )
