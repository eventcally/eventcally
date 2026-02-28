from flask import redirect

from project.domain.commands import DeleteEventPlaceCommand
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.views.manage_admin_unit.event_place.forms import (
    CreateEventPlaceForm,
    DeleteEventPlaceForm,
    UpdateEventPlaceForm,
)
from project.views.utils import handle_base_error


class CreateView(BaseCreateView):
    form_class = CreateEventPlaceForm

    @handle_base_error
    def dispatch_validated_form(self, form: CreateEventPlaceForm, object, **kwargs):
        from project.views.utils import current_admin_unit

        cmd = form.create_create_command(current_admin_unit.id)
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))


class UpdateView(BaseUpdateView):
    form_class = UpdateEventPlaceForm

    @handle_base_error
    def dispatch_validated_form(self, form: UpdateEventPlaceForm, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    form_class = DeleteEventPlaceForm

    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteEventPlaceCommand.model_construct(id=object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
