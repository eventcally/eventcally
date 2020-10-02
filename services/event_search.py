from dateutils import today, date_add_time, date_set_end_of_day, form_input_from_date, form_input_to_date
from dateutil.relativedelta import relativedelta
from flask import request

class EventSearchParams(object):

    def __init__(self):
        self._date_from = None
        self._date_to = None
        self._date_from_str = None
        self._date_to_str = None
        self.admin_unit_id = None
        self.keyword = None
        self.latitude = None
        self.longitude = None
        self.distance = None

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

    def set_default_date_range(self):
        self.date_from = today
        self.date_to = date_set_end_of_day(today + relativedelta(months=12))

    def load_from_request(self):
        if 'date_from' in request.args:
            self.date_from_str = request.args['date_from']

        if 'date_to' in request.args:
            self.date_to_str = request.args['date_to']

        if 'keyword' in request.args:
            self.keyword = request.args['keyword']

        if "coordinate" in request.args:
            coordinate = request.args['coordinate']
            if coordinate is not None and len(coordinate) > 0:
                (self.latitude, self.longitude) = coordinate.split(",")

        if "distance" in request.args:
            self.distance = request.args['distance']
