from dateutil.relativedelta import relativedelta

from project.dateutils import date_set_end_of_day, form_input_from_date, get_today


class EventSearchParams(object):
    """The data the event search forms are filled from and populate; the search
    itself runs on `EventSearchCriteria` (`criteria_from_search_params`)."""

    def __init__(self):
        self.created_at_from = None
        self.created_at_to = None
        self.updated_at_from = None
        self.updated_at_to = None
        self.last_modified_at_from = None
        self.last_modified_at_to = None
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
        self.weekday = None
        self.status = None
        self.public_status = None
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

    @property
    def date_to_str(self):
        return self._date_to_str

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
