from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteOrganizationDueForDeletionHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.DeleteOrganizationDueForDeletionCommand,
        uow: AbstractUnitOfWork,
    ) -> bool:
        """Skips (returns False) organizations that are gone or whose deletion
        request was cancelled or is still within the grace period."""
        organization = uow.organizations.get(cmd.organization_id)

        if organization is None or not organization.is_deletion_due():
            return False

        organization.delete(cmd.actor)
        uow.organizations.remove(organization)
        return True
