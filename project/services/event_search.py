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
        self.keyword = None
        self.latitude = None
        self.longitude = None
        self.distance = None
        self.category_id = None
        self.organizer_id = None
        self.weekday = None

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
        self._date_to = form_input_to_date(value)

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
        self.date_to = date_set_end_of_day(today + relativedelta(months=12))

    def set_planing_date_range(self):
        today = get_today()
        self.date_from = today
        self.date_to = date_set_end_of_day(today + relativedelta(months=3))

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
            category_ids = request.args.getlist("category_id")
            if "0" in category_ids:
                category_ids.remove("0")
            if len(category_ids) > 0:
                self.category_id = category_ids

        if "weekday" in request.args:
            self.weekday = request.args.getlist("weekday")

        if "organizer_id" in request.args:
            self.organizer_id = request.args["organizer_id"]
