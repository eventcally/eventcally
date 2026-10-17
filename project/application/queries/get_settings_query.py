from project.application.queries.base import Query
from project.application.read_models.settings_read_model import SettingsReadModel


class GetSettingsQuery(Query[SettingsReadModel]):
    """The site settings; empty values when there is no settings row. Public: the
    texts are shown on public pages, and the planning calendars are only reached
    through the (access checked) planning views."""
