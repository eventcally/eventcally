from typing import Optional

from project.domain.models.aggregates.settings_aggregate import SettingsAggregate
from project.domain.repositories.abstract_settings_repository import (
    AbstractSettingsRepository,
)
from project.models.settings import Settings


class SqlAlchemySettingsRepository(AbstractSettingsRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_model(self) -> Optional[Settings]:
        return self.session.query(Settings).first()

    def _add(self, settings: SettingsAggregate):
        model = Settings.from_aggregate(settings)
        self.session.add(model)
        self.session.flush()

        settings.id = model.id

    def _update(self, settings: SettingsAggregate):
        model = self._get_model()
        model.fill_from_aggregate(settings)
        self.session.merge(model)
        self.session.flush()

    def _get(self) -> Optional[SettingsAggregate]:
        model = self._get_model()
        return Settings.to_aggregate(model) if model else None
