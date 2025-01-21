from flask_babel import gettext

from project.models.admin_unit import AdminUnitMemberRole
from project.modular.base_views import BaseCreateView, BaseUpdateView
from project.views.utils import send_template_mail_async


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.roles.choices = [
            (c.name, gettext(c.title))
            for c in AdminUnitMemberRole.query.order_by(AdminUnitMemberRole.id).all()
        ]

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    def after_commit(self, object, form):
        send_template_mail_async(
            object.email,
            "invitation_notice",
            invitation=object,
        )


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    def render_template(self, form, object, **kwargs):
        form.roles.data = object.roles.split(",") if object.roles else None

        return super().render_template(form=form, object=object, **kwargs)
