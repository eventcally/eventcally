import abc

from project.application.read_models.settings_read_model import SettingsReadModel
from project.application.read_models.site_notices_read_model import SiteNoticesReadModel


class AbstractSiteSettingsReadRepository(abc.ABC):
    @abc.abstractmethod
    def get_site_notices(self) -> SiteNoticesReadModel:  # pragma: no cover
        """Empty notices when no settings row exists."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_settings(self) -> SettingsReadModel:  # pragma: no cover
        """Empty settings when no settings row exists."""
        raise NotImplementedError
