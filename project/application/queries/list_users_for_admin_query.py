from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.page import Page
from project.application.read_models.user_admin_read_models import UserAdminReadModel


class ListUsersForAdminQuery(Query[Page[UserAdminReadModel]]):
    """Users by email (case-insensitive). Platform admins only."""

    page: PageRequest = PageRequest()
