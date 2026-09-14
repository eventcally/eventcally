from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_relation_utils import ensure_organization_relation_exists


class DeleteOrganizationRelationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeleteOrganizationRelationCommand, uow: AbstractUnitOfWork
    ):
        organization_relation = ensure_organization_relation_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            organization_relation.source_admin_unit_id,
            "outgoing_organization_relations:write",
            uow,
        )

        organization_relation.delete(cmd.actor)
        uow.organization_relations.remove(organization_relation)
