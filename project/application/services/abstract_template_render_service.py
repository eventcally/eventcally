import abc


class AbstractTemplateRenderService(abc.ABC):
    @abc.abstractmethod
    def render_template(
        self, template_name_or_list: str | list[str], **context
    ) -> str:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def render_template_with_locale(
        self, locale, template_name_or_list: str | list[str], **context
    ) -> str:  # pragma: no cover
        raise NotImplementedError
