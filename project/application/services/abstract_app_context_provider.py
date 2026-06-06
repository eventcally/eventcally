import abc

from project.domain.models.entities.actor import Actor


class AbstractAppContextProvider(abc.ABC):
    @abc.abstractmethod
    def get_current_actor(self) -> Actor:  # pragma: no cover
        raise NotImplementedError
