from flask import redirect

from project.application.commands import WithdrawOrganizationVerificationRequestCommand
from project.modular.base_views import BaseDeleteView, BaseListView
from project.views import utils
from project.views.utils import handle_base_error


class ListView(BaseListView):
    def get_docs_url(self, **kwargs):  # pragma: no cover
        return utils.get_docs_url("/goto/organization-verify", **kwargs)


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = WithdrawOrganizationVerificationRequestCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
