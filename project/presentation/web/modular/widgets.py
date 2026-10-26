from flask import request
from flask_babel import gettext
from wtforms.widgets.core import Select


class AjaxSelect2Widget(Select):
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault("data-role", "select2-ajax")
        kwargs.setdefault("data-url", f"{request.base_url}?field_name={field.name}")

        allow_blank = getattr(field, "allow_blank", False)
        if allow_blank and not self.multiple:  # pragma: no cover
            kwargs["data-allow-blank"] = "1"

        placeholder = field.loader.placeholder or gettext("Please select")
        kwargs.setdefault("data-placeholder", placeholder)

        kwargs.setdefault(
            "data-minimum-input-length", field.loader.minimum_input_length
        )

        if self.multiple:
            kwargs["data-multiple"] = "1"

        return super().__call__(field, **kwargs)
