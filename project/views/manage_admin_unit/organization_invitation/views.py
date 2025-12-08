from project.modular.base_views import BaseCreateView, BaseUpdateView
from project.views.utils import current_admin_unit


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not current_admin_unit.can_verify_other:
            del form.relation_verify

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    pass


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    pass
