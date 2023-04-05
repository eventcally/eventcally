from dateutil.relativedelta import relativedelta
from flask import request

from project.dateutils import (
    date_set_end_of_day,
    form_input_from_date,
    form_input_to_date,
    get_today,
)


class EventSearchParams(object):
    def __init__(self):
        self._date_from = None
        self._date_to = None
        self._date_from_str = None
        self._date_to_str = None
        self._coordinate = None
        self.admin_unit_id = None
        self.can_read_private_events = None
        self.keyword = None
        self.latitude = None
        self.longitude = None
        self.distance = None
        self.category_id = None
        self.organizer_id = None
        self.event_place_id = None
        self.event_list_id = None
        self.weekday = None
        self.sort = None
        self.status = None
        self.favored_by_user_id = None

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

    def set_planing_date_range(self):
        today = get_today()
        self.date_from = today
        self.date_to = date_set_end_of_day(today + relativedelta(months=3))

    def load_list_param(self, param: str):
        item_ids = request.args.getlist(param)

        if "0" in item_ids:
            item_ids.remove("0")

        if len(item_ids) > 0:
            return item_ids

        return None

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

    def load_from_request(self):
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

        if "weekday" in request.args:
            self.weekday = request.args.getlist("weekday")

        if "organizer_id" in request.args:
            self.organizer_id = request.args["organizer_id"]

        if "event_place_id" in request.args:
            self.event_place_id = request.args["event_place_id"]

        if "event_list_id" in request.args:
            self.event_list_id = self.load_list_param("event_list_id")

        if "sort" in request.args:
            self.sort = request.args["sort"]

        if "organization_id" in request.args:
            self.admin_unit_id = request.args["organization_id"]

        if "status" in request.args:
            self.status = self.load_status_list_param()
