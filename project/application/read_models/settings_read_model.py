from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class SettingsReadModel(BaseReadModel):
    """The site settings as the legal pages, start page and the admin forms read them.
    All fields are `None` when no settings row exists."""

    model_config = ConfigDict(frozen=True)

    tos: Optional[str] = None
    legal_notice: Optional[str] = None
    contact: Optional[str] = None
    privacy: Optional[str] = None
    start_page: Optional[str] = None
    announcement: Optional[str] = None
    planning_external_calendars: Optional[str] = None
