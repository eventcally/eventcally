from project.domain.types import ObjectId

from .base import CommandWithResult


class DeleteOldEventCommand(CommandWithResult[bool]):
    """System command for the nightly purge; authorized by the deletion rule, not
    the actor. Returns whether a row was deleted."""

    event_id: ObjectId
