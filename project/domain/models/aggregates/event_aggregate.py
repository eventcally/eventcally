from __future__ import annotations

import datetime
from typing import List, Optional

from project.domain.errors.constraint_error import ConstraintError
from project.domain.events.event_created import EventCreated
from project.domain.events.event_deleted import EventDeleted
from project.domain.events.event_updated import EventUpdated
from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types import unset
from project.domain.types.changed_value import ChangedValue
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class EventAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    organizer_id: ObjectId
    event_place_id: ObjectId
    date_definitions: List[EventDateDefinitionValueObject]
    dates: List[EventDateEntity] = []
    status: EventStatus = EventStatus.scheduled
    public_status: EventPublicStatus = EventPublicStatus.published
    description: Optional[str] = None
    external_link: Optional[str] = None
    ticket_link: Optional[str] = None
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    kid_friendly: Optional[bool] = None
    accessible_for_free: Optional[bool] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    registration_required: Optional[bool] = None
    booked_up: Optional[bool] = None
    expected_participants: Optional[int] = None
    price_info: Optional[str] = None
    target_group_origin: Optional[EventTargetGroupOrigin] = None
    attendance_mode: Optional[EventAttendanceMode] = None
    photo: Optional[ImageEntity] = None
    previous_start_date: Optional[datetime.datetime] = None
    category_ids: Optional[List[ObjectId]] = None
    custom_category_ids: Optional[List[ObjectId]] = None
    rating: Optional[int] = None
    co_organizer_ids: Optional[List[ObjectId]] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        name: str,
        organizer_id: ObjectId,
        event_place_id: ObjectId,
        date_definitions: List[EventDateDefinitionValueObject],
        status: EventStatus,
        public_status: EventPublicStatus,
        description: Optional[str] = None,
        external_link: Optional[str] = None,
        ticket_link: Optional[str] = None,
        tags: Optional[str] = None,
        internal_tags: Optional[str] = None,
        kid_friendly: Optional[bool] = None,
        accessible_for_free: Optional[bool] = None,
        age_from: Optional[int] = None,
        age_to: Optional[int] = None,
        registration_required: Optional[bool] = None,
        booked_up: Optional[bool] = None,
        expected_participants: Optional[int] = None,
        price_info: Optional[str] = None,
        target_group_origin: Optional[EventTargetGroupOrigin] = None,
        attendance_mode: Optional[EventAttendanceMode] = None,
        photo: Optional[ImageEntity] = None,
        previous_start_date: Optional[datetime.datetime] = None,
        category_ids: Optional[List[ObjectId]] = None,
        custom_category_ids: Optional[List[ObjectId]] = None,
        rating: Optional[int] = None,
        co_organizer_ids: Optional[List[ObjectId]] = None,
    ) -> EventAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            name=name,
            organizer_id=organizer_id,
            event_place_id=event_place_id,
            date_definitions=date_definitions,
            status=status,
            public_status=public_status,
            description=description,
            external_link=external_link,
            ticket_link=ticket_link,
            tags=tags,
            internal_tags=internal_tags,
            kid_friendly=kid_friendly,
            accessible_for_free=accessible_for_free,
            age_from=age_from,
            age_to=age_to,
            registration_required=registration_required,
            booked_up=booked_up,
            expected_participants=expected_participants,
            price_info=price_info,
            target_group_origin=target_group_origin,
            attendance_mode=attendance_mode,
            photo=photo,
            previous_start_date=previous_start_date,
            category_ids=category_ids,
            custom_category_ids=custom_category_ids,
            rating=rating,
            co_organizer_ids=co_organizer_ids,
        )
        instance.validate_instance()
        instance.update_event_dates_with_recurrence_rule()

        event = EventCreated(
            actor=actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            name=instance.name,
            organizer_id=instance.organizer_id,
            event_place_id=instance.event_place_id,
            date_definitions=instance.date_definitions,
            dates=instance.dates,
            status=instance.status,
            public_status=instance.public_status,
            description=instance.description,
            external_link=instance.external_link,
            ticket_link=instance.ticket_link,
            tags=instance.tags.replace(" ", "") if instance.tags else None,
            internal_tags=(
                instance.internal_tags.replace(" ", "")
                if instance.internal_tags
                else None
            ),
            kid_friendly=instance.kid_friendly,
            accessible_for_free=instance.accessible_for_free,
            age_from=instance.age_from,
            age_to=instance.age_to,
            registration_required=instance.registration_required,
            booked_up=instance.booked_up,
            expected_participants=instance.expected_participants,
            price_info=instance.price_info,
            target_group_origin=instance.target_group_origin,
            attendance_mode=instance.attendance_mode,
            previous_start_date=instance.previous_start_date,
            category_ids=instance.category_ids,
            custom_category_ids=instance.custom_category_ids,
            rating=instance.rating,
            co_organizer_ids=instance.co_organizer_ids,
            photo=(
                ImageForEvent.from_image_entity(instance.photo)
                if instance.photo
                else None
            ),
        )

        instance.domain_events.append(event)
        return instance

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
        organizer_id: Unsetable[ObjectId] = unset,
        event_place_id: Unsetable[ObjectId] = unset,
        date_definitions: Unsetable[List[EventDateDefinitionValueObject]] = unset,
        status: Unsetable[EventStatus] = unset,
        public_status: Unsetable[EventPublicStatus] = unset,
        description: NullableUnsetable[str] = unset,
        external_link: NullableUnsetable[str] = unset,
        ticket_link: NullableUnsetable[str] = unset,
        tags: NullableUnsetable[str] = unset,
        internal_tags: NullableUnsetable[str] = unset,
        kid_friendly: NullableUnsetable[bool] = unset,
        accessible_for_free: NullableUnsetable[bool] = unset,
        age_from: NullableUnsetable[int] = unset,
        age_to: NullableUnsetable[int] = unset,
        registration_required: NullableUnsetable[bool] = unset,
        booked_up: NullableUnsetable[bool] = unset,
        expected_participants: NullableUnsetable[int] = unset,
        price_info: NullableUnsetable[str] = unset,
        target_group_origin: NullableUnsetable[EventTargetGroupOrigin] = unset,
        attendance_mode: NullableUnsetable[EventAttendanceMode] = unset,
        photo: NullableUnsetable[ImageEntity] = unset,
        previous_start_date: NullableUnsetable[datetime.datetime] = unset,
        category_ids: NullableUnsetable[List[ObjectId]] = unset,
        custom_category_ids: NullableUnsetable[List[ObjectId]] = unset,
        rating: NullableUnsetable[int] = unset,
        co_organizer_ids: NullableUnsetable[List[ObjectId]] = unset,
    ):
        event = EventUpdated(actor=actor, id=self.id, admin_unit_id=self.admin_unit_id)

        self._update_field_with_value("name", name, event)
        self._update_field_with_value("organizer_id", organizer_id, event)
        self._update_field_with_value("event_place_id", event_place_id, event)
        self._update_field_with_value("status", status, event)
        self._update_field_with_value("public_status", public_status, event)
        self._update_field_with_value("description", description, event)
        self._update_field_with_value("external_link", external_link, event)
        self._update_field_with_value("ticket_link", ticket_link, event)
        self._update_field_with_value(
            "tags", tags.replace(" ", "") if tags else None, event
        )
        self._update_field_with_value(
            "internal_tags",
            internal_tags.replace(" ", "") if internal_tags else None,
            event,
        )
        self._update_field_with_value("kid_friendly", kid_friendly, event)
        self._update_field_with_value("accessible_for_free", accessible_for_free, event)
        self._update_field_with_value("age_from", age_from, event)
        self._update_field_with_value("age_to", age_to, event)
        self._update_field_with_value(
            "registration_required", registration_required, event
        )
        self._update_field_with_value("booked_up", booked_up, event)
        self._update_field_with_value(
            "expected_participants", expected_participants, event
        )
        self._update_field_with_value("price_info", price_info, event)
        self._update_field_with_value("target_group_origin", target_group_origin, event)
        self._update_field_with_value("attendance_mode", attendance_mode, event)
        self._update_field_with_value("previous_start_date", previous_start_date, event)
        self._update_field_with_value("rating", rating, event)
        self._update_field_with_value("category_ids", category_ids, event)
        self._update_field_with_value("custom_category_ids", custom_category_ids, event)
        self._update_field_with_value("co_organizer_ids", co_organizer_ids, event)
        date_definitions_changed = self._update_field_with_value(
            "date_definitions", date_definitions, event
        )

        old_photo_for_event = (
            ImageForEvent.from_image_entity(self.photo) if self.photo else None
        )
        if self._update_field_with_value("photo", photo):
            new_photo_for_event = (
                ImageForEvent.from_image_entity(self.photo) if self.photo else None
            )
            event.photo = ChangedValue(old=old_photo_for_event, new=new_photo_for_event)

        self.validate_instance()

        if date_definitions_changed:
            self.update_event_dates_with_recurrence_rule()

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete(self, actor: Actor):
        self.domain_events.append(
            EventDeleted(actor=actor, id=self.id, admin_unit_id=self.admin_unit_id)
        )

    def validate_instance(self):
        if not self.date_definitions:
            raise ConstraintError("At least one date defintion is required.")

        if self.co_organizer_ids and self.organizer_id in self.co_organizer_ids:
            raise ConstraintError("Invalid co-organizer.")

    def update_event_dates_with_recurrence_rule(self):
        from dateutil.relativedelta import relativedelta

        from project.domain.dateutils import (
            date_add_time,
            date_set_begin_of_day,
            date_set_end_of_day,
            dates_from_recurrence_rule,
        )

        dates_to_add = list()
        dates_to_remove = list(self.dates)

        for date_definition in self.date_definitions:
            if date_definition.allday:
                date_definition.start = date_set_begin_of_day(date_definition.start)
                if date_definition.end:
                    date_definition.end = date_set_end_of_day(date_definition.end)

            start = date_definition.start
            end = date_definition.end

            if end:
                time_difference = relativedelta(end, start)

            if date_definition.recurrence_rule:
                rr_dates = dates_from_recurrence_rule(
                    start, date_definition.recurrence_rule
                )
            else:
                rr_dates = [start]

            for rr_date in rr_dates:
                rr_date_start = date_add_time(
                    rr_date, start.hour, start.minute, start.second, rr_date.tzinfo
                )

                if end:
                    rr_date_end = rr_date_start + time_difference
                else:
                    rr_date_end = None

                existing_date = next(
                    (
                        date
                        for date in self.dates
                        if date.start == rr_date_start
                        and date.end == rr_date_end
                        and date.allday == date_definition.allday
                    ),
                    None,
                )
                if existing_date:
                    if existing_date in dates_to_remove:
                        dates_to_remove.remove(existing_date)
                else:
                    new_date = EventDateEntity.model_construct(
                        id=-1,
                        start=rr_date_start,
                        end=rr_date_end,
                        allday=date_definition.allday,
                    )
                    dates_to_add.append(new_date)

        self.dates = [date for date in self.dates if date not in dates_to_remove]
        self.dates.extend(dates_to_add)
