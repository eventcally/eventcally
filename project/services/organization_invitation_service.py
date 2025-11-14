from project.models import AdminUnitInvitation
from project.models.admin_unit import AdminUnit, AdminUnitRelation
from project.services.base_service import BaseService
from project.views.utils import send_template_mail_async


class OrganizationInvitationService(BaseService[AdminUnitInvitation]):

    def insert_object(self, object: AdminUnitInvitation):
        super().insert_object(object)

        send_template_mail_async(
            object.email,
            "organization_invitation_notice",
            invitation=object,
        )

    def send_admin_unit_invitation_accepted_mails(
        self,
        invitation: AdminUnitInvitation,
        relation: AdminUnitRelation,
        admin_unit: AdminUnit,
    ):
        from project.views.utils import send_template_mails_to_admin_unit_members_async

        # Benachrichtige alle Mitglieder der AdminUnit, die diese Einladung erstellt hatte
        send_template_mails_to_admin_unit_members_async(
            invitation.admin_unit_id,
            "organization_invitations:write",
            "organization_invitation_accepted_notice",
            invitation=invitation,
            relation=relation,
            admin_unit=admin_unit,
        )
