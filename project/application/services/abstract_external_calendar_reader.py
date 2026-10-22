import abc
from datetime import date
from typing import List

from project.application.read_models.external_calendar_read_models import (
    ExternalCalendarEventReadModel,
)


class AbstractExternalCalendarReader(abc.ABC):
    @abc.abstractmethod
    def list_events(
        self, url: str, start: date, end: date
    ) -> List[ExternalCalendarEventReadModel]:  # pragma: no cover
        """Fetches the iCal feed at `url` and expands the events between the dates.

        Raises `ExternalCalendarError` when the feed cannot be loaded or parsed."""
        raise NotImplementedError
