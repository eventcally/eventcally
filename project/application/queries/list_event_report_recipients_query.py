from typing import List

from project.application.queries.base import Query
from project.application.read_models.access_helper_read_models import (
    MailRecipientReadModel,
)
from project.domain.types.object_id import ObjectId


class ListEventReportRecipientsQuery(Query[List[MailRecipientReadModel]]):
    """Who is mailed about a reported event of the organization: members who may write
    events plus platform admins. Trusted: no actor check (the public report endpoint
    calls it)."""

    admin_unit_id: ObjectId
