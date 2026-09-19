from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import (
    ensure_actor_has_permission_for_admin_unit,
    ensure_actor_is_authenticated_user,
)
from .invitation_utils import (
    ensure_actor_is_invitation_receiver,
    ensure_organization_invitation_exists,
)
from .organization_utils import ensure_organization_exists


class CreateOrganizationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.CreateOrganizationCommand, uow: AbstractUnitOfWork
    ) -> commands.CreateOrganizationCommandResult:
        # Every path makes the actor the new organization's admin member, so
        # the actor has to be a user on all of them — including the plain
        # create path, which has no admin unit to check a permission against.
        # (Whether a given user may create an organization at all is the
        # `ADMIN_UNIT_CREATE_REQUIRES_ADMIN` policy, checked by the view: it
        # reads Flask config, which this layer must not import.)
        ensure_actor_is_authenticated_user(cmd.actor, uow)

        logo = ImageEntity.from_value_object(cmd.logo)

        organization = OrganizationAggregate.create(
            actor=cmd.actor,
            name=cmd.name,
            short_name=cmd.short_name,
            description=cmd.description,
            url=cmd.url,
            email=cmd.email,
            phone=cmd.phone,
            fax=cmd.fax,
            location=cmd.location,
            logo=logo,
        )
        uow.organizations.add(organization)

        member = OrganisationMemberAggregate.create(
            admin_unit_id=organization.id,
            user_id=cmd.actor.user_id,
            roles=["admin", "event_verifier"],
        )
        uow.organization_members.add(member)

        organizer = EventOrganizerAggregate.create(
            actor=cmd.actor,
            admin_unit_id=organization.id,
            name=cmd.name,
            url=cmd.url,
            email=cmd.email,
            phone=cmd.phone,
            fax=cmd.fax,
            location=cmd.location,
            logo=logo,
        )
        uow.event_organizers.add(organizer)

        if cmd.location:
            place = EventPlaceAggregate.create(
                actor=cmd.actor,
                admin_unit_id=organization.id,
                name=cmd.location.city,
                location=cmd.location,
            )
            uow.event_places.add(place)

        relation = None

        if cmd.invitation_id is not None:
            invitation = ensure_organization_invitation_exists(cmd.invitation_id, uow)
            ensure_actor_is_invitation_receiver(cmd.actor, invitation.email, uow)
            inviting_organization = ensure_organization_exists(
                invitation.admin_unit_id, uow
            )

            relation = OrganizationRelationAggregate.create(
                actor=cmd.actor,
                source_admin_unit_id=invitation.admin_unit_id,
                target_admin_unit_id=organization.id,
                verify=(
                    inviting_organization.can_verify_other
                    and invitation.relation_verify
                ),
                auto_verify_event_reference_requests=(
                    inviting_organization.incoming_reference_requests_allowed
                    and invitation.relation_auto_verify_event_reference_requests
                ),
                invited=True,
                accepted_invitation_email=invitation.email,
                target_admin_unit_name=cmd.name,
            )
            uow.organization_relations.add(relation)
            uow.organization_invitations.remove(invitation)
        elif cmd.current_admin_unit_id is not None:
            # The relation is created on behalf of the current organization and
            # may mark the new one as verified by it, so the actor has to hold
            # the same permission the creating view checks before offering it.
            ensure_actor_has_permission_for_admin_unit(
                cmd.actor,
                cmd.current_admin_unit_id,
                "outgoing_organization_relations:write",
                uow,
            )
            current_organization = ensure_organization_exists(
                cmd.current_admin_unit_id, uow
            )
            verify = (
                cmd.embedded_relation_verify and current_organization.can_verify_other
            )
            auto_verify = (
                cmd.embedded_relation_auto_verify_event_reference_requests
                and current_organization.incoming_reference_requests_allowed
            )

            if verify or auto_verify:
                relation = OrganizationRelationAggregate.create(
                    actor=cmd.actor,
                    source_admin_unit_id=cmd.current_admin_unit_id,
                    target_admin_unit_id=organization.id,
                    verify=verify,
                    auto_verify_event_reference_requests=auto_verify,
                )
                uow.organization_relations.add(relation)

        return commands.CreateOrganizationCommandResult(
            id=organization.id, verified=bool(relation and relation.verify)
        )
