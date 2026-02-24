from flask import redirect

from project.domain.commands import DeleteEventOrganizerCommand
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.views.manage_admin_unit.event_organizer.forms import (
    CreateEventOrganizerForm,
    DeleteEventOrganizerForm,
    UpdateEventOrganizerForm,
)
from project.views.utils import handle_base_error


class CreateView(BaseCreateView):
    form_class = CreateEventOrganizerForm

    @handle_base_error
    def dispatch_validated_form(self, form: CreateEventOrganizerForm, object, **kwargs):
        from project.views.utils import current_admin_unit

        cmd = form.create_create_command(current_admin_unit.id)
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))


class UpdateView(BaseUpdateView):
    form_class = UpdateEventOrganizerForm

    @handle_base_error
    def dispatch_validated_form(self, form: UpdateEventOrganizerForm, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    form_class = DeleteEventOrganizerForm

    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteEventOrganizerCommand.model_construct(id=object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
