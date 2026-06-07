from flask_babel import force_locale, gettext

from project.application.services.abstract_localization_service import (
    AbstractLocalizationService,
)


class FlaskBabelLocalizationService(AbstractLocalizationService):
    def get_text(self, *args, **kwargs) -> str:
        return gettext(*args, **kwargs)

    def get_text_with_locale(self, locale, *args, **kwargs) -> str:
        with force_locale(locale):
            return gettext(*args, **kwargs)
