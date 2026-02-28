from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .organization_utils import ensure_organization_exists


class RequestOrganizationDeletionHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.RequestOrganizationDeletionCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            organization = ensure_organization_exists(cmd.id, uow)
            organization.request_deletion(cmd)
            uow.commit()
