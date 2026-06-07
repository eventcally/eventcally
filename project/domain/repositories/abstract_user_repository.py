import abc
from typing import Optional, Set

from project.domain.models.aggregates.user_aggregate import UserAggregate


class AbstractUserRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[UserAggregate] = set()

    def get(self, id: int) -> Optional[UserAggregate]:
        user = self._get(id)
        if user:
            self.seen.add(user)
        return user

    def get_all_with_ids(self, object_ids: list[int]) -> list[UserAggregate]:
        users = self._get_all_with_ids(object_ids)
        self.seen.update(users)
        return users

    @abc.abstractmethod
    def _get(self, object_id: int) -> Optional[UserAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_all_with_ids(
        self, object_ids: list[int]
    ) -> list[UserAggregate]:  # pragma: no cover
        raise NotImplementedError
