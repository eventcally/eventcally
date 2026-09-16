import abc


class AbstractAppKeyGenerator(abc.ABC):
    @abc.abstractmethod
    def generate(self) -> tuple[str, str, str, str]:  # pragma: no cover
        """Returns (checksum, kid, public_key, private_pem)."""
        raise NotImplementedError
