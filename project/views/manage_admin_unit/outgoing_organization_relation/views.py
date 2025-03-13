from flask import request

from project.modular.base_views import BaseCreateView, BaseListView, BaseUpdateView
from project.views.utils import current_admin_unit


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not current_admin_unit.can_verify_other:
            del form.verify

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not form.is_submitted():
            target = request.args.get("target", 0, type=int)
            form.target_admin_unit.process_formdata([target])

            if form.verify:
                verify = request.args.get("verify", 0, type=int)
                if verify == 1:
                    form.verify.data = True

        return form


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    pass


class ListView(SharedFormViewMixin, BaseListView):
    def create_display(self, **kwargs):
        display = super().create_display(**kwargs)

        if not current_admin_unit.can_verify_other:
            del display.verify

        return display
