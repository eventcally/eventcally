from typing import Optional

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class GetMemberInvitationRecipientQuery(Query[Optional[str]]):
    """The email an invitation was sent to, or `None`. Public: the invitation link
    must work before the recipient has signed in or registered."""

    id: ObjectId
