import abc
from typing import Set

from project.models import AppInstallation
from project.models.oauth import OAuth2Client


class AbstractAppRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OAuth2Client | AppInstallation] = set()

    def add(self, app: OAuth2Client):
        self._add(app)
        self.seen.add(app)

    def get(self, object_id: int) -> OAuth2Client:
        app = self._get(object_id)
        if app:
            self.seen.add(app)
        return app

    def remove(self, app: OAuth2Client):
        self._remove(app)
        self.seen.add(app)

    def add_app_installation(self, app_installation: AppInstallation):
        self._add_app_installation(app_installation)
        self.seen.add(app_installation)

    def get_app_installation(self, object_id: int) -> AppInstallation:
        app_installation = self._get_app_installation(object_id)
        if app_installation:
            self.seen.add(app_installation)
        return app_installation

    def remove_app_installation(self, app_installation: AppInstallation):
        self._remove_app_installation(app_installation)
        self.seen.add(app_installation)

    @abc.abstractmethod
    def _add(self, app: OAuth2Client):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> OAuth2Client:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, app: OAuth2Client):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _add_app_installation(
        self, app_installation: AppInstallation
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_app_installation(
        self, object_id: int
    ) -> AppInstallation:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove_app_installation(
        self, app_installation: AppInstallation
    ):  # pragma: no cover
        raise NotImplementedError
