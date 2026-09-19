from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_utils import ensure_organization_exists


class UpdateOrganizationHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateOrganizationCommand, uow: AbstractUnitOfWork):
        organization = ensure_organization_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, organization.id, "settings:write", uow
        )

        organization.update(
            actor=cmd.actor,
            name=cmd.name,
            short_name=cmd.short_name,
            description=cmd.description,
            url=cmd.url,
            email=cmd.email,
            phone=cmd.phone,
            fax=cmd.fax,
            location=cmd.location,
            logo=ImageEntity.from_nullable_unsetable_value_object(cmd.logo),
            incoming_verification_requests_allowed=cmd.incoming_verification_requests_allowed,
            incoming_verification_requests_text=cmd.incoming_verification_requests_text,
            incoming_verification_requests_postal_codes=cmd.incoming_verification_requests_postal_codes,
        )
        uow.organizations.update(organization)
