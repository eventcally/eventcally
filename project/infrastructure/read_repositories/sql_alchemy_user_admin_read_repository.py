from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from project.application.queries.page_request import PageRequest
from project.application.read_models.page import Page
from project.application.read_models.user_admin_read_models import (
    NewsletterRecipientReadModel,
    RoleReadModel,
    UserAdminReadModel,
)
from project.application.read_repositories.abstract_user_admin_read_repository import (
    AbstractUserAdminReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import Role, User
from project.infrastructure.read_repositories.query_helpers import count


class SqlAlchemyUserAdminReadRepository(AbstractUserAdminReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def list_users(self, page_request: PageRequest) -> Page[UserAdminReadModel]:
        base = select(User).options(selectinload(User.roles))
        users = (
            self.session.execute(
                base.order_by(func.lower(User.email), User.id)
                .limit(page_request.per_page)
                .offset(page_request.offset)
            )
            .scalars()
            .all()
        )
        return Page[UserAdminReadModel](
            items=[_to_user(user) for user in users],
            page=page_request.page,
            per_page=page_request.per_page,
            total=count(self.session, select(User.id)),
        )

    def get_user(self, user_id: ObjectId) -> Optional[UserAdminReadModel]:
        user = self.session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.roles))
        ).scalar_one_or_none()
        return _to_user(user) if user else None

    def list_roles(self) -> List[RoleReadModel]:
        roles = self.session.execute(select(Role).order_by(Role.id)).scalars().all()
        return [RoleReadModel(id=r.id, name=r.name, title=r.title) for r in roles]

    def list_newsletter_recipients(self) -> List[NewsletterRecipientReadModel]:
        users = (
            self.session.execute(
                select(User)
                .where(
                    User.email.is_not(None),
                    User.confirmed_at.is_not(None),
                    User.newsletter_enabled,
                )
                .order_by(User.id)
            )
            .scalars()
            .all()
        )
        return [
            NewsletterRecipientReadModel(id=u.id, email=u.email, locale=u.locale)
            for u in users
        ]


def _to_user(user) -> UserAdminReadModel:
    return UserAdminReadModel(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        confirmed_at=user.confirmed_at,
        tos_accepted_at=user.tos_accepted_at,
        deletion_requested_at=user.deletion_requested_at,
        roles=[role.name for role in user.roles],
    )
