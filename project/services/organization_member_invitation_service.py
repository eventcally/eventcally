from project.models.admin_unit import AdminUnitMemberInvitation
from project.services.base_service import BaseService
from project.views.utils import send_template_mail_async


class OrganizationMemberInvitationService(BaseService[AdminUnitMemberInvitation]):

    def insert_object(self, object: AdminUnitMemberInvitation):
        super().insert_object(object)

        send_template_mail_async(
            object.email,
            "invitation_notice",
            invitation=object,
        )
