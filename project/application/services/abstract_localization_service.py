import abc


class AbstractLocalizationService(abc.ABC):
    @abc.abstractmethod
    def get_text(self, *args, **kwargs) -> str:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_text_with_locale(self, locale, *args, **kwargs) -> str:  # pragma: no cover
        raise NotImplementedError
