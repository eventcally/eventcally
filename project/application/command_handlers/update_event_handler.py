from project.application.command_handlers.event_organizer_utils import (
    ensure_event_organizer_exists,
)
from project.application.command_handlers.event_place_utils import (
    ensure_event_place_exists,
)
from project.application.command_handlers.event_utils import ensure_event_exists
from project.application.commands import UpdateEventCommand
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors.constraint_error import ConstraintError
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.types import unset

from .abstract_command_handler import AbstractCommandHandler


class UpdateEventHandler(AbstractCommandHandler):
    def handle(self, cmd: UpdateEventCommand, uow: AbstractUnitOfWork):
        with uow:
            event = ensure_event_exists(cmd.id, uow)

            if cmd.organizer_id != unset:
                event_organizer = ensure_event_organizer_exists(cmd.organizer_id, uow)
                if event_organizer.admin_unit_id != event.admin_unit_id:
                    raise ConstraintError("Invalid organizer.")

            if cmd.co_organizer_ids and cmd.co_organizer_ids != unset:
                for co_organizer_id in cmd.co_organizer_ids:
                    co_organizer = ensure_event_organizer_exists(co_organizer_id, uow)
                    if co_organizer.admin_unit_id != event.admin_unit_id:
                        raise ConstraintError("Invalid co-organizer.")

            if cmd.event_place_id != unset:
                event_place = ensure_event_place_exists(cmd.event_place_id, uow)
                if event_place.admin_unit_id != event.admin_unit_id:
                    raise ConstraintError("Invalid place.")

            event.update(
                actor=cmd.actor,
                name=cmd.name,
                organizer_id=cmd.organizer_id,
                event_place_id=cmd.event_place_id,
                date_definitions=cmd.date_definitions,
                status=cmd.status,
                public_status=cmd.public_status,
                description=cmd.description,
                external_link=cmd.external_link,
                ticket_link=cmd.ticket_link,
                tags=cmd.tags,
                internal_tags=cmd.internal_tags,
                kid_friendly=cmd.kid_friendly,
                accessible_for_free=cmd.accessible_for_free,
                age_from=cmd.age_from,
                age_to=cmd.age_to,
                registration_required=cmd.registration_required,
                booked_up=cmd.booked_up,
                expected_participants=cmd.expected_participants,
                price_info=cmd.price_info,
                target_group_origin=cmd.target_group_origin,
                attendance_mode=cmd.attendance_mode,
                photo=ImageEntity.from_nullable_unsetable_value_object(cmd.photo),
                previous_start_date=cmd.previous_start_date,
                category_ids=cmd.category_ids,
                custom_category_ids=cmd.custom_category_ids,
                rating=cmd.rating,
                co_organizer_ids=cmd.co_organizer_ids,
            )
            uow.events.update(event)
            uow.commit()
