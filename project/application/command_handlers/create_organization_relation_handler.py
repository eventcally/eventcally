from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class CreateOrganizationRelationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.CreateOrganizationRelationCommand, uow: AbstractUnitOfWork
    ):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            cmd.source_admin_unit_id,
            "outgoing_organization_relations:write",
            uow,
        )

        organization_relation = OrganizationRelationAggregate.create(
            actor=cmd.actor,
            source_admin_unit_id=cmd.source_admin_unit_id,
            target_admin_unit_id=cmd.target_admin_unit_id,
            auto_verify_event_reference_requests=cmd.auto_verify_event_reference_requests,
            verify=cmd.verify,
        )
        uow.organization_relations.add(organization_relation)

        return commands.CreateOrganizationRelationCommandResult(
            id=organization_relation.id
        )
