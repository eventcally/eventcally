import abc
from typing import Optional

from project.application.queries.list_app_installations_for_app_query import (
    ListAppInstallationsForAppQuery,
)
from project.application.queries.list_app_installations_query import (
    ListAppInstallationsQuery,
)
from project.application.queries.list_user_app_installations_query import (
    ListUserAppInstallationsQuery,
)
from project.application.read_models.app_installation_read_models import (
    AppInstallationReadModel,
    InstallableAppReadModel,
    UserAppInstallationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractAppInstallationReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListAppInstallationsQuery
    ) -> Page[AppInstallationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[AppInstallationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_installable_app(
        self, object_id: ObjectId
    ) -> Optional[InstallableAppReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_for_user(
        self, query: ListUserAppInstallationsQuery
    ) -> Page[UserAppInstallationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_for_app(
        self, query: ListAppInstallationsForAppQuery
    ) -> Page[AppInstallationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_for_app(
        self, app_id: ObjectId, object_id: ObjectId
    ) -> Optional[AppInstallationReadModel]:  # pragma: no cover
        raise NotImplementedError
