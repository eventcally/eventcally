from project.application.queries.base import Query
from project.application.read_models.site_notices_read_model import SiteNoticesReadModel


class GetSiteNoticesQuery(Query[SiteNoticesReadModel]):
    """ToS flag and announcement from the site settings. Public."""
