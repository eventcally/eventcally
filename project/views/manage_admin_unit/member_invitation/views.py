from flask import redirect
from flask_babel import gettext

from project.application.commands import RevokeMemberInvitationCommand
from project.models.admin_unit import AdminUnitMemberRole
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.views.utils import current_admin_unit, handle_base_error


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.roles.choices = [
            (c.name, gettext(c.title))
            for c in AdminUnitMemberRole.query.order_by(AdminUnitMemberRole.id).all()
        ]

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_create_command(admin_unit_id=current_admin_unit.id)
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    def render_template(self, form, object, **kwargs):
        form.roles.data = object.roles.split(",") if object.roles else None

        return super().render_template(form=form, object=object, **kwargs)

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = RevokeMemberInvitationCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
