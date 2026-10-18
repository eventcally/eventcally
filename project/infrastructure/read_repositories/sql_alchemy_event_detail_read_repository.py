from typing import List, Optional

from sqlalchemy import select

from project.application.queries.page_request import PageRequest
from project.application.read_models.event_read_models import (
    EventDateDetailReadModel,
    EventDateListItemReadModel,
    EventDateReadModel,
    EventDetailReadModel,
    EventEditReadModel,
)
from project.application.read_models.event_visibility_read_model import (
    EventVisibilityReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import Event, EventDate
from project.infrastructure.read_repositories.event_read_model_mappers import (
    event_edit_load_options,
    event_load_options,
    event_reference_requests,
    event_references,
    reference_ids,
    to_event_detail,
    to_event_edit,
    verified_admin_units,
)
from project.infrastructure.read_repositories.query_helpers import paginate
from project.shared.dateutils import get_today


class SqlAlchemyEventDetailReadRepository(AbstractEventDetailReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def get_visibility(self, event_id: ObjectId) -> Optional[EventVisibilityReadModel]:
        row = self.session.execute(
            select(Event.id, Event.public_status, Event.admin_unit_id).where(
                Event.id == event_id
            )
        ).one_or_none()

        return self._to_visibility(row)

    def get_visibility_of_date(
        self, event_date_id: ObjectId
    ) -> Optional[EventVisibilityReadModel]:
        row = self.session.execute(
            select(Event.id, Event.public_status, Event.admin_unit_id)
            .join(EventDate, EventDate.event_id == Event.id)
            .where(EventDate.id == event_date_id)
        ).one_or_none()

        return self._to_visibility(row)

    def _to_visibility(self, row) -> Optional[EventVisibilityReadModel]:
        if row is None:
            return None

        verified = verified_admin_units(self.session, {row.admin_unit_id})
        return EventVisibilityReadModel(
            event_id=row.id,
            public_status=row.public_status,
            admin_unit_id=row.admin_unit_id,
            admin_unit_is_verified=verified.get(row.admin_unit_id, False),
        )

    def get_detail(
        self, event_id: ObjectId, reference_admin_unit_id: Optional[ObjectId]
    ) -> Optional[EventDetailReadModel]:
        event = self.session.execute(
            select(Event)
            .where(Event.id == event_id)
            .options(*event_load_options(co_organizers=True, audit=True))
        ).scalar_one_or_none()

        if event is None:
            return None

        return self._to_detail(event, reference_admin_unit_id)

    def _to_detail(self, event, reference_admin_unit_id) -> EventDetailReadModel:
        verified = verified_admin_units(self.session, {event.admin_unit_id})
        references = reference_ids(self.session, {event.id}, reference_admin_unit_id)

        return to_event_detail(
            event,
            verified.get(event.admin_unit_id, False),
            references.get(event.id),
            event_references(self.session, {event.id}).get(event.id),
            event_reference_requests(self.session, {event.id}).get(event.id),
        )

    def get_for_edit(self, event_id: ObjectId) -> Optional[EventEditReadModel]:
        event = self.session.execute(
            select(Event)
            .where(Event.id == event_id)
            .options(*event_edit_load_options())
        ).scalar_one_or_none()

        if event is None:
            return None

        verified = verified_admin_units(self.session, {event.admin_unit_id})
        return to_event_edit(event, verified.get(event.admin_unit_id, False))

    def get_date_detail(
        self, event_date_id: ObjectId
    ) -> Optional[EventDateDetailReadModel]:
        row = self.session.execute(
            select(
                EventDate.id,
                EventDate.start,
                EventDate.end,
                EventDate.allday,
                EventDate.event_id,
            ).where(EventDate.id == event_date_id)
        ).one_or_none()

        if row is None:
            return None

        event = self.get_detail(row.event_id, None)

        return EventDateDetailReadModel(
            id=row.id, start=row.start, end=row.end, allday=row.allday, event=event
        )

    def list_dates_of_event(
        self, event_id: ObjectId, page_request: PageRequest
    ) -> Page[EventDateListItemReadModel]:
        filters = [EventDate.event_id == event_id]

        return paginate(
            self.session,
            select(EventDate.id, EventDate.start)
            .where(*filters)
            .order_by(EventDate.start, EventDate.id),
            select(EventDate.id).where(*filters),
            page_request,
            lambda row: EventDateListItemReadModel(id=row.id, start=row.start),
        )

    def list_upcoming_dates(self, event_id: ObjectId) -> List[EventDateReadModel]:
        rows = self.session.execute(
            select(EventDate.id, EventDate.start, EventDate.end, EventDate.allday)
            .where(EventDate.event_id == event_id, EventDate.start >= get_today())
            .order_by(EventDate.start, EventDate.id)
        ).all()

        return [
            EventDateReadModel(id=r.id, start=r.start, end=r.end, allday=r.allday)
            for r in rows
        ]
