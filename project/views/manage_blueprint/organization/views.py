from flask import flash, redirect, request, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import current_user

from project import db
from project.access import can_create_admin_unit, has_access
from project.models import AdminUnitInvitation
from project.modular.base_views import BaseCreateView
from project.services.admin_unit import (
    add_relation,
    insert_admin_unit_for_user,
    send_admin_unit_invitation_accepted_mails,
)
from project.utils import strings_are_equal_ignoring_case
from project.views.manage_blueprint.organization.forms import CreateForm
from project.views.utils import (
    flash_message,
    get_current_admin_unit,
    permission_missing,
)


class CreateView(BaseCreateView):
    form_class = CreateForm

    def check_access(self, **kwargs):
        response = super().check_access(**kwargs)
        if response:  # pragma: no cover
            return response

        invitation = None

        invitation_id = (
            int(request.args.get("invitation_id"))
            if "invitation_id" in request.args
            else 0
        )
        if invitation_id > 0:
            invitation = AdminUnitInvitation.query.get_or_404(invitation_id)

            if not strings_are_equal_ignoring_case(
                invitation.email, current_user.email
            ):
                return permission_missing(url_for("manage_admin_units"))

        if not invitation:
            if not can_create_admin_unit():
                flash_message(
                    gettext(
                        "Organizations cannot currently be created. The project is in a closed test phase. If you are interested, you can contact us."
                    ),
                    url_for("contact"),
                    gettext("Contact"),
                    "danger",
                )
                return redirect(url_for("manage_admin_units"))

            if current_user.deletion_requested_at:  # pragma: no cover
                flash(gettext("Your account is scheduled for deletion."), "danger")
                return redirect(url_for("profile"))

        self.invitation = invitation
        self.current_admin_unit = get_current_admin_unit()
        self.embedded_relation_enabled = (
            not invitation
            and self.current_admin_unit
            and has_access(self.current_admin_unit, "admin_unit:update")
            and (
                self.current_admin_unit.can_verify_other
                or self.current_admin_unit.incoming_reference_requests_allowed
            )
        )

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if self.embedded_relation_enabled:
            form.embedded_relation.label.text = lazy_gettext(
                "Relation to %(admin_unit_name)s",
                admin_unit_name=self.current_admin_unit.name,
            )

            if not self.current_admin_unit.can_verify_other:
                del form.embedded_relation.form.verify
            elif not form.is_submitted():
                form.embedded_relation.form.verify.data = True

            if not self.current_admin_unit.incoming_reference_requests_allowed:
                del form.embedded_relation.form.auto_verify_event_reference_requests

        else:
            del form.embedded_relation

        if self.invitation and not form.is_submitted():
            form.name.data = self.invitation.admin_unit_name

        return form

    def insert_object(self, admin_unit):
        _, _, self.relation = insert_admin_unit_for_user(
            admin_unit, current_user, self.invitation
        )

    def after_commit(self, admin_unit, form):
        super().after_commit(admin_unit, form)

        if self.embedded_relation_enabled:
            self.relation = add_relation(admin_unit, form, self.current_admin_unit)

        if self.invitation and self.relation:
            send_admin_unit_invitation_accepted_mails(
                self.invitation, self.relation, admin_unit
            )

        if self.invitation:
            db.session.delete(self.invitation)
            db.session.commit()

        if not self.relation or not self.relation.verify:
            flash(
                gettext(
                    "The organization is not verified. Events are therefore not publicly visible."
                ),
                "warning",
            )

    def get_redirect_url(self, object, **kwargs):
        admin_unit = object

        if self.relation and self.relation.verify:
            return url_for("manage_admin_unit", id=admin_unit.id)

        return url_for(
            "manage_admin_unit.outgoing_admin_unit_verification_requests",
            id=admin_unit.id,
        )
