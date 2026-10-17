from typing import List

from project.application.queries.base import Query
from project.application.read_models.user_admin_read_models import (
    NewsletterRecipientReadModel,
)


class ListNewsletterRecipientsQuery(Query[List[NewsletterRecipientReadModel]]):
    """Confirmed users who enabled the newsletter. Platform admins only."""

    pass
