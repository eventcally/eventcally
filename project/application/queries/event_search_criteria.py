from datetime import datetime
from enum import Enum
from typing import List, Optional

from project.application.queries.trackable_criteria import TrackableCriteria
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.object_id import ObjectId


class EventSearchSort(str, Enum):
    """The API `sort` values of the event searches (`start` is the default order)."""

    start = "start"
    created_at_desc = "-created_at"
    updated_at_desc = "-updated_at"
    last_modified_at_desc = "-last_modified_at"
    rating_desc = "-rating"
    reference_created_at_desc = "-reference_created_at"


class EventSearchCriteria(CustomBaseModel):
    """What the event and event-date searches filter by.

    Visibility is not a criterion: drafts and planned events are included only for
    callers the handler finds permitted (`include_private`, `include_planned`).
    """

    trackable: TrackableCriteria = TrackableCriteria()
    keyword: Optional[str] = None
    # Matches the event name like `parse_like_term` (the manage list's keyword).
    name: Optional[str] = None
    category_ids: List[int] = []
    custom_category_set_ids: List[int] = []
    status: List[EventStatus] = []
    public_status: List[EventPublicStatus] = []
    organizer_id: Optional[ObjectId] = None
    event_place_id: Optional[ObjectId] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance: Optional[int] = None
    postal_codes: List[str] = []
    tags: List[str] = []
    internal_tags: List[str] = []
    weekdays: List[int] = []
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    exclude_recurring: bool = False
    is_recurring: Optional[bool] = None
    expected_participants_min: Optional[int] = None
    admin_unit_id: Optional[ObjectId] = None
    include_admin_unit_references: bool = False
    admin_unit_references_only: bool = False
    not_referenced_by_admin_unit_id: Optional[ObjectId] = None
    # The caller asks for the private events of `admin_unit_id`; granted only to
    # actors with `events:read` there.
    include_private: bool = False
    # The caller asks for planned events; granted only to actors who may plan.
    include_planned: bool = False
    sort: Optional[EventSearchSort] = None
