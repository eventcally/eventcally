from project.domain.types import ObjectId

from .base import Command


class ReportEventCommand(Command):
    """Mails the organization members who may write events, plus platform admins,
    about a reported event. Public, trusted endpoint: no actor authorization."""

    event_id: ObjectId
    contact_name: str
    contact_email: str
    message: str
