from flask import redirect, url_for
from flask_babel import gettext
from flask_security import current_user

from project.models.admin_unit import AdminUnitMemberRole
from project.modular.base_views import BaseDeleteView, BaseUpdateView
from project.services.admin_unit import add_roles_to_admin_unit_member
from project.views.utils import current_admin_unit


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

    def complete_object(self, object, form):
        super().complete_object(object, form)

        member = object
        member.roles.clear()
        add_roles_to_admin_unit_member(member, form.role_names.data)

        if member.user_id == current_user.id and not current_user.has_role("admin"):
            add_roles_to_admin_unit_member(member, ["admin"])


class DeleteView(BaseDeleteView):
    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.user_id == current_user.id:
            return redirect(
                url_for("manage_admin_unit_delete_membership", id=current_admin_unit.id)
            )

        return None
