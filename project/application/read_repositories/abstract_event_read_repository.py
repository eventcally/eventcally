import abc

from project.application.read_models.event_read_model import EventReadModel


class AbstractEventReadRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, object_id: int) -> EventReadModel:  # pragma: no cover
        raise NotImplementedError
