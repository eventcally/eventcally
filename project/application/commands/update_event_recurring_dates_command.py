from project.domain.types import ObjectId

from .base import Command


class UpdateEventRecurringDatesCommand(Command):
    """Brings the dates of an event in line with its (recurring) date definitions.
    Issued by the nightly job with the system actor; no domain event is raised."""

    event_id: ObjectId
