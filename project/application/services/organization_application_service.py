from project.application.services.abstract_email_service import AbstractEmailService
from project.domain.abstract_unit_of_work import AbstractUnitOfWork


class OrganizationApplicationService:
    def __init__(
        self,
        email_service: AbstractEmailService,
    ):
        self.email_service = email_service

    def send_template_mails_to_members_async(
        self, uow: AbstractUnitOfWork, admin_unit_id, permission, template, **context
    ):
        members = uow.organization_members.get_all_with_permission(
            admin_unit_id, permission
        )
        user_ids = [member.user_id for member in members]
        users = uow.users.get_all_with_ids(user_ids)
        self.email_service.send_template_mails_to_users_async(
            users, template, **context
        )
