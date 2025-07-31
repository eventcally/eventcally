from typing import Type

from dateutil.relativedelta import relativedelta
from flask import request
from sqlalchemy import and_

from project.dateutils import (
    date_set_end_of_day,
    form_input_from_date,
    form_input_to_date,
    get_today,
)
from project.models.trackable_mixin import TrackableMixin


class BaseSearchParams(object):
    def __init__(self):
        self.sort = None

    def load_from_request(self, **kwargs):
        self.sort = kwargs.get("sort", self.sort)

    def load_list_param(self, param: str):
        item_ids = request.args.getlist(param)

        if len(item_ids) == 1 and "," in item_ids[0]:
            item_ids = [i.strip() for i in item_ids[0].split(",")]

        if "0" in item_ids:
            item_ids.remove("0")

        if len(item_ids) > 0:
            return item_ids

        return None

    def load_bool_param(self, param: str):
        return request.args[param].lower() in ("true", "t", "yes", "y", "on", "1")


class TrackableSearchParams(BaseSearchParams):
    def __init__(self):
        super().__init__()
        self.created_at_from = None
        self.created_at_to = None

    def load_from_request(self, **kwargs):
        super().load_from_request(**kwargs)

        self.created_at_from = kwargs.get("created_at_from", self.created_at_from)
        self.created_at_to = kwargs.get("created_at_to", self.created_at_to)

    def get_trackable_query(self, query, klass: Type[TrackableMixin]):
        filter = self.fill_trackable_filter(1 == 1, klass)
        return query.filter(filter)

    def fill_trackable_filter(self, filter, klass: Type[TrackableMixin]):
        if self.created_at_from:
            filter = and_(filter, klass.created_at >= self.created_at_from)

        if self.created_at_to:
            filter = and_(filter, klass.created_at < self.created_at_to)

        return filter

    def get_trackable_order_by(self, query, klass: Type[TrackableMixin]):
        if self.sort == "-created_at":
            query = query.order_by(klass.created_at.desc())
        elif self.sort == "-updated_at":
            query = query.order_by(klass.updated_at.desc().nulls_last())
        elif self.sort == "-last_modified_at":
            query = query.order_by(klass.last_modified_at.desc())

        return query


class EventReferenceSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self.admin_unit_id = None


class EventReferenceRequestSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self.admin_unit_id = None
        self.review_status = None


class AdminUnitVerificationRequestSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self.source_admin_unit_id = None
        self.target_admin_unit_id = None
        self.review_status = None


class AdminUnitSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self.keyword = None
        self.include_unverified = False
        self.only_verifier = False
        self.reference_request_for_admin_unit_id = None
        self.incoming_verification_requests_postal_code = None
        self.postal_code = None

    def load_from_request(self, **kwargs):
        super().load_from_request(**kwargs)

        self.keyword = kwargs.get("keyword", self.keyword)

        if "postal_code" in request.args:
            self.postal_code = self.load_list_param("postal_code")


class OrganizerSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self.admin_unit_id = None
        self.name = None

    def load_from_request(self, **kwargs):
        super().load_from_request(**kwargs)

        self.name = kwargs.get("name", self.name)


class EventPlaceSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self.admin_unit_id = None
        self.name = None

    def load_from_request(self, **kwargs):
        super().load_from_request(**kwargs)

        self.name = kwargs.get("name", self.name)


class EventSearchParams(TrackableSearchParams):
    def __init__(self):
        super().__init__()
        self._date_from = None
        self._date_to = None
        self._date_from_str = None
        self._date_to_str = None
        self._coordinate = None
        self.admin_unit_id = None
        self.include_admin_unit_references = None
        self.admin_unit_references_only = None
        self.can_read_private_events = None
        self.can_read_planned_events = None
        self.keyword = None
        self.latitude = None
        self.longitude = None
        self.distance = None
        self.category_id = None
        self.custom_category_set_id = None
        self.organizer_id = None
        self.event_place_id = None
        self.event_list_id = None
        self.weekday = None
        self.status = None
        self.public_status = None
        self.favored_by_user_id = None
        self.postal_code = None
        self.not_referenced_by_organization_id = None
        self.exclude_recurring = False
        self.expected_participants_min = None
        self.sort = "start"
        self.tag = None
        self.internal_tag = None

    @property
    def date_from(self):
        return self._date_from

    @date_from.setter
    def date_from(self, value):
        self._date_from = value
        self._date_from_str = form_input_from_date(value)

    @property
    def date_to(self):
        return self._date_to

    @date_to.setter
    def date_to(self, value):
        self._date_to = value
        self._date_to_str = form_input_from_date(value)

    @property
    def date_from_str(self):
        return self._date_from_str

    @date_from_str.setter
    def date_from_str(self, value):
        self._date_from_str = value
        self._date_from = form_input_to_date(value)

    @property
    def date_to_str(self):
        return self._date_to_str

    @date_to_str.setter
    def date_to_str(self, value):
        self._date_to_str = value
        self._date_to = form_input_to_date(value, 23, 59, 59)

    @property
    def coordinate(self):
        return self._coordinate

    @coordinate.setter
    def coordinate(self, value):
        self._coordinate = value
        if value is not None and len(value) > 0:
            (self.latitude, self.longitude) = value.split(",")
        else:
            self.latitude = None
            self.longitude = None

    def set_default_date_range(self):
        today = get_today()
        self.date_from = today
        self.date_to = None

    def set_planning_date_range(self):
        today = get_today()
        self.date_from = today
        self.date_to = date_set_end_of_day(today + relativedelta(months=3))

    def load_status_list_param(self):
        stati = self.load_list_param("status")

        if stati is None:  # pragma: no cover
            return None

        from project.models import EventStatus

        result = list()

        for status in stati:
            if status in EventStatus.__members__:
                result.append(EventStatus.__members__[status])

        return result

    def load_public_status_list_param(self):
        public_stati = self.load_list_param("public_status")

        if public_stati is None:  # pragma: no cover
            return None

        from project.models import PublicStatus

        result = list()

        for public_status in public_stati:
            if public_status in PublicStatus.__members__:
                result.append(PublicStatus.__members__[public_status])

        return result

    def load_from_request(self, **kwargs):
        super().load_from_request(**kwargs)

        if "date_from" in request.args:
            self.date_from_str = request.args["date_from"]

        if "date_to" in request.args:
            self.date_to_str = request.args["date_to"]

        if "keyword" in request.args:
            self.keyword = request.args["keyword"]

        if "coordinate" in request.args:
            self.coordinate = request.args["coordinate"]

        if "distance" in request.args:
            self.distance = request.args["distance"]

        if "category_id" in request.args:
            self.category_id = self.load_list_param("category_id")

        if "custom_category_set_id" in request.args:
            self.custom_category_set_id = self.load_list_param("custom_category_set_id")

        if "weekday" in request.args:
            self.weekday = request.args.getlist("weekday")

        if "organizer_id" in request.args:
            self.organizer_id = request.args["organizer_id"]

        if "event_place_id" in request.args:
            self.event_place_id = request.args["event_place_id"]

        if "expected_participants_min" in request.args:
            self.expected_participants_min = request.args["expected_participants_min"]

        if "event_list_id" in request.args:
            self.event_list_id = self.load_list_param("event_list_id")

        if "postal_code" in request.args:
            self.postal_code = self.load_list_param("postal_code")

        if "tag" in request.args:
            self.tag = self.load_list_param("tag")

        if "internal_tag" in request.args:
            self.internal_tag = self.load_list_param("internal_tag")

        if "organization_id" in request.args:
            self.admin_unit_id = request.args["organization_id"]

        if "admin_unit_id" in request.args:
            self.admin_unit_id = request.args["admin_unit_id"]

        if "status" in request.args:
            self.status = self.load_status_list_param()

        if "public_status" in request.args:
            self.public_status = self.load_public_status_list_param()

        if "exclude_recurring" in request.args:
            self.exclude_recurring = self.load_bool_param("exclude_recurring")

        if "include_organization_references" in request.args:
            self.include_admin_unit_references = self.load_bool_param(
                "include_organization_references"
            )

        if "organization_references_only" in request.args:
            self.admin_unit_references_only = self.load_bool_param(
                "organization_references_only"
            )
