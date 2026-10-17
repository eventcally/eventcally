from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class SiteNoticesReadModel(BaseReadModel):
    """What every page shows from the site settings: the ToS link flag (footer,
    registration form) and the announcement banner."""

    model_config = ConfigDict(frozen=True)

    has_tos: bool = False
    announcement: Optional[str] = None
