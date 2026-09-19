import abc


class AbstractApiKeyGenerator(abc.ABC):
    @abc.abstractmethod
    def generate(self) -> tuple[str, str]:  # pragma: no cover
        raise NotImplementedError
