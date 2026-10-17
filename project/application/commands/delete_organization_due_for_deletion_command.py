from project.domain.types import ObjectId

from .base import CommandWithResult


class DeleteOrganizationDueForDeletionCommand(CommandWithResult[bool]):
    """System command for the nightly purge; authorized by the deletion rule, not
    the actor. Returns whether a row was deleted."""

    organization_id: ObjectId
