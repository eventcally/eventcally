from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_relation_utils import ensure_organization_relation_exists


class UpdateOrganizationRelationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateOrganizationRelationCommand, uow: AbstractUnitOfWork
    ):
        organization_relation = ensure_organization_relation_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            organization_relation.source_admin_unit_id,
            "outgoing_organization_relations:write",
            uow,
        )

        organization_relation.update(
            actor=cmd.actor,
            auto_verify_event_reference_requests=cmd.auto_verify_event_reference_requests,
            verify=cmd.verify,
        )
        uow.organization_relations.update(organization_relation)
