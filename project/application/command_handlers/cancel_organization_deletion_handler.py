from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .organization_utils import ensure_organization_exists


class CancelOrganizationDeletionHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.CancelOrganizationDeletionCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            organization = ensure_organization_exists(cmd.id, uow)
            organization.cancel_deletion(cmd.actor)
            uow.organizations.update(organization)
            uow.commit()
