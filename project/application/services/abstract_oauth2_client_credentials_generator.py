import abc


class AbstractOAuth2ClientCredentialsGenerator(abc.ABC):
    @abc.abstractmethod
    def generate(self) -> tuple[str, str]:  # pragma: no cover
        raise NotImplementedError
