from flask import redirect, url_for
from flask_babel import gettext
from flask_security import current_user

from project.application.commands import RemoveOrganizationMemberCommand
from project.models.admin_unit import AdminUnitMemberRole
from project.modular.base_views import BaseDeleteView, BaseUpdateView
from project.views.utils import handle_base_error


class UpdateView(BaseUpdateView):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.role_names.choices = [
            (c.name, gettext(c.title))
            for c in AdminUnitMemberRole.query.order_by(AdminUnitMemberRole.id).all()
        ]

        return form

    def render_template(self, form, object, **kwargs):
        form.role_names.data = [c.name for c in object.roles]

        return super().render_template(form=form, object=object, **kwargs)

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.user_id == current_user.id:
            return redirect(
                url_for(
                    "user.organization_member_delete", organization_member_id=object.id
                )
            )

        return None

    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = RemoveOrganizationMemberCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
