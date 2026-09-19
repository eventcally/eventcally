from typing import Optional

from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.domain.repositories import AbstractApiKeyRepository
from project.domain.types import ObjectId
from project.infrastructure.sql_error_translation import flush
from project.models.api_key import ApiKey


class SqlAlchemyApiKeyRepository(AbstractApiKeyRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, api_key: ApiKeyAggregate):
        model = ApiKey.from_aggregate(api_key)
        self.session.add(model)
        flush(self.session)

        api_key.id = model.id

    def _update(self, api_key: ApiKeyAggregate):
        model = self._get_model(api_key.id)
        model.fill_from_aggregate(api_key)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[ApiKey]:
        return self.session.query(ApiKey).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[ApiKeyAggregate]:
        model = self._get_model(object_id)
        return ApiKey.to_aggregate(model) if model else None

    def _remove(self, api_key: ApiKeyAggregate):
        model = self._get_model(api_key.id)
        self.session.delete(model)

    def _count_for_owner(
        self, user_id: Optional[ObjectId], admin_unit_id: Optional[ObjectId]
    ) -> int:
        return (
            self.session.query(ApiKey)
            .filter_by(user_id=user_id, admin_unit_id=admin_unit_id)
            .count()
        )
