import abc

from project.application.read_models.event_read_model import EventReadModel
from project.domain.types.object_id import ObjectId


class AbstractEventReadRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, object_id: int) -> EventReadModel:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_organizer_names(
        self, object_ids: set[ObjectId]
    ) -> dict[ObjectId, str]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_place_names(
        self, object_ids: set[ObjectId]
    ) -> dict[ObjectId, str]:  # pragma: no cover
        raise NotImplementedError
