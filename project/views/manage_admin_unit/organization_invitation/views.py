from project.modular.base_views import BaseCreateView, BaseUpdateView
from project.views.utils import current_admin_unit, send_template_mail_async


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not current_admin_unit.can_verify_other:
            del form.relation_verify

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    def after_commit(self, object, form):
        send_template_mail_async(
            object.email,
            "organization_invitation_notice",
            invitation=object,
        )


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    pass
