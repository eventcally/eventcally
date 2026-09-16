from typing import Optional

from project.domain.models.aggregates.app_key_aggregate import AppKeyAggregate
from project.domain.repositories import AbstractAppKeyRepository
from project.infrastructure.sql_error_translation import flush
from project.models.app import AppKey


class SqlAlchemyAppKeyRepository(AbstractAppKeyRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, app_key: AppKeyAggregate):
        model = AppKey.from_aggregate(app_key)
        self.session.add(model)
        flush(self.session)

        app_key.id = model.id

    def _get_model(self, object_id: int) -> Optional[AppKey]:
        return self.session.query(AppKey).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[AppKeyAggregate]:
        model = self._get_model(object_id)
        return AppKey.to_aggregate(model) if model else None

    def _remove(self, app_key: AppKeyAggregate):
        model = self._get_model(app_key.id)
        self.session.delete(model)
