from flask import render_template
from flask_babel import force_locale

from project.application.services.abstract_template_render_service import (
    AbstractTemplateRenderService,
)


class FlaskTemplateRenderService(AbstractTemplateRenderService):
    def render_template(self, template_name_or_list: str | list[str], **context) -> str:
        return render_template(template_name_or_list, **context)

    def render_template_with_locale(
        self, locale, template_name_or_list: str | list[str], **context
    ) -> str:
        with force_locale(locale):
            return render_template(template_name_or_list, **context)
