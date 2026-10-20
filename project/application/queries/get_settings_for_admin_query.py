from project.application.queries.base import Query
from project.application.read_models.settings_read_model import SettingsReadModel


class GetSettingsForAdminQuery(Query[SettingsReadModel]):
    """The site settings incl. the planning calendars, for the admin forms; empty
    values when there is no settings row. Platform admins only."""
