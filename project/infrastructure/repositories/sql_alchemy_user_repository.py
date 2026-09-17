from typing import Optional

from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.repositories.abstract_user_repository import AbstractUserRepository
from project.models.user import User


class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_model(self, object_id: int) -> Optional[User]:
        return self.session.query(User).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[UserAggregate]:
        model = self._get_model(object_id)
        return User.to_aggregate(model)

    def _get_all_with_ids(self, object_ids: list[int]) -> list[UserAggregate]:
        models = self.session.query(User).filter(User.id.in_(object_ids)).all()
        return [User.to_aggregate(m) for m in models]

    def _update(self, user: UserAggregate):
        model = self._get_model(user.id)
        model.fill_from_aggregate(user)
        self.session.merge(model)
        self.session.flush()

    def _remove(self, user: UserAggregate):
        model = self._get_model(user.id)
        self.session.delete(model)

    def _reset_tos_accepted_for_all(self) -> int:
        return self.session.query(User).update(
            {"tos_accepted_at": None}, synchronize_session=False
        )
