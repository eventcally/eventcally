from sqlalchemy import select

from project.application.read_models.settings_read_model import SettingsReadModel
from project.application.read_models.site_notices_read_model import SiteNoticesReadModel
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)
from project.models import Settings


class SqlAlchemySiteSettingsReadRepository(AbstractSiteSettingsReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def get_site_notices(self) -> SiteNoticesReadModel:
        # The columns are deferred on the model; selecting them avoids `undefer`.
        row = self.session.execute(
            select(Settings.tos, Settings.announcement).order_by(Settings.id).limit(1)
        ).one_or_none()

        if row is None:
            return SiteNoticesReadModel()

        return SiteNoticesReadModel(
            has_tos=bool(row.tos), announcement=row.announcement or None
        )

    def get_settings(self) -> SettingsReadModel:
        row = self.session.execute(
            select(
                Settings.tos,
                Settings.legal_notice,
                Settings.contact,
                Settings.privacy,
                Settings.start_page,
                Settings.announcement,
                Settings.planning_external_calendars,
            )
            .order_by(Settings.id)
            .limit(1)
        ).one_or_none()

        return SettingsReadModel(**row._asdict()) if row else SettingsReadModel()
