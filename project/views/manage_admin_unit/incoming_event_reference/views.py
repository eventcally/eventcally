from flask import redirect, url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup

from project.application.commands import DeleteEventReferenceCommand
from project.modular.base_views import BaseDeleteView, BaseListView, BaseUpdateView
from project.views.manage_admin_unit.incoming_event_reference.forms import (
    DeleteEventReferenceForm,
    UpdateEventReferenceForm,
)
from project.views.utils import handle_base_error


class UpdateView(BaseUpdateView):
    form_class = UpdateEventReferenceForm

    @handle_base_error
    def dispatch_validated_form(self, form: UpdateEventReferenceForm, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    form_class = DeleteEventReferenceForm

    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteEventReferenceCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())


class ListView(BaseListView):
    def get_instruction(self, **kwargs):
        reference_open = "&quot;"
        reference_close = "&quot;"
        reference_title = gettext("Reference event")

        search_open = '<a href="%s">' % url_for("main.event_dates")
        search_close = "</a>"

        return Markup(
            lazy_gettext(
                "Here you can find events from other organizations that you referenced. To reference an event, select %(reference_open)s%(reference_title)s%(reference_close)s on an event page that you can find through the %(search_open)ssearch%(search_close)s.",
                reference_open=reference_open,
                reference_close=reference_close,
                reference_title=reference_title,
                search_open=search_open,
                search_close=search_close,
            )
        )
