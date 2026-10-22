"""Read models of external (iCal) calendars."""

from datetime import date, datetime
from typing import Optional, Union

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class ExternalCalendarEventReadModel(BaseReadModel):
    """One occurrence of an iCal event. `start`/`end` are plain dates for all-day events."""

    model_config = ConfigDict(frozen=True)

    name: str
    start: Union[datetime, date]
    end: Optional[Union[datetime, date]] = None
    allday: bool
    location: Optional[str] = None
    description: Optional[str] = None
