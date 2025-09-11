from project.modular.base_views import BaseCreateView, BaseUpdateView
from project.permissions import organization_app_permission_infos


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.app_permissions.choices = [
            (i.permission, i.label) for i in organization_app_permission_infos
        ]

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    pass


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    pass
