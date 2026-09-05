import abc


class AbstractUrlProvider(abc.ABC):
    @abc.abstractmethod
    def get_image_url(self, image_id: int, image_hash: int) -> str:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_site_url(self) -> str:  # pragma: no cover
        raise NotImplementedError
