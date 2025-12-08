from flask_babel import gettext

from project.models.admin_unit import AdminUnitMemberRole
from project.modular.base_views import BaseCreateView, BaseUpdateView


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.roles.choices = [
            (c.name, gettext(c.title))
            for c in AdminUnitMemberRole.query.order_by(AdminUnitMemberRole.id).all()
        ]

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    pass


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    def render_template(self, form, object, **kwargs):
        form.roles.data = object.roles.split(",") if object.roles else None

        return super().render_template(form=form, object=object, **kwargs)
