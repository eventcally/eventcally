from flask import json, request, url_for
from flask_babel import gettext
from markupsafe import Markup
from wtforms.widgets import TextInput, html_params


class GooglePlaceWidget(object):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("data-role", "google-place")
        kwargs.setdefault("data-url", f"{request.base_url}?field_name={field.name}")
        kwargs.setdefault("data-placeholder", gettext("Search location on Google"))
        kwargs.setdefault("class", "form-control")

        if field.location_only:
            kwargs.setdefault("data-location-only", "1")

        return Markup(
            '<div class="input-group-prepend"><span class="input-group-text"><span><i class="fab fa-google"></i></span></span></div><select %s></select>'
            % html_params(**kwargs)
        )


class AjaxValidationWidget(TextInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("data-role", "ajax-validation")
        kwargs.setdefault("data-url", f"{request.base_url}?field_name={field.name}")
        return super().__call__(field, **kwargs)


class AjaxSelect2Widget(object):
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault("data-role", "select2-ajax")
        kwargs.setdefault("data-url", url_for(request.endpoint, field_name=field.name))

        allow_blank = getattr(field, "allow_blank", False)
        if allow_blank and not self.multiple:  # pragma: no cover
            kwargs["data-allow-blank"] = "1"

        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", "hidden")

        if self.multiple:  # pragma: no cover
            result = []
            ids = []

            for value in field.data:
                data = field.loader.format(value)
                result.append(data)
                ids.append(str(data[0]))

            separator = getattr(field, "separator", ",")

            kwargs["value"] = separator.join(ids)
            kwargs["data-json"] = json.dumps(result)
            kwargs["data-multiple"] = "1"
        else:
            data = field.loader.format(field.data)

            if data:
                kwargs["value"] = data[0]
                kwargs["data-json"] = json.dumps(data)

        placeholder = field.loader.options.get("placeholder", gettext("Please select"))
        kwargs.setdefault("data-placeholder", placeholder)

        minimum_input_length = int(field.loader.options.get("minimum_input_length", 1))
        kwargs.setdefault("data-minimum-input-length", minimum_input_length)

        return Markup("<select %s></select>" % html_params(name=field.name, **kwargs))
