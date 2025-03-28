from flask import request
from flask_babel import gettext
from markupsafe import Markup
from wtforms.widgets import TextInput, html_params
from wtforms.widgets.core import Select


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


class GooglePlaceCoordinateWidget(Select):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("name", field.name)
        kwargs.setdefault("data-role", "google-place-coordinate")
        kwargs.setdefault("data-url", f"{request.base_url}?field_name={field.name}")
        kwargs.setdefault("data-placeholder", gettext("Search location on Google"))
        kwargs.setdefault("class", "form-control")

        html = []
        html.append("<div %s>" % html_params(class_="input-group-prepend"))
        html.append(
            '<span class="input-group-text"><span><i class="fab fa-google"></i></span></span>'
        )
        html.append("</div>")

        html.append("<select %s>" % html_params(**kwargs))
        for val, label, selected in field.iter_choices():
            html.append(self.render_option(val, label, selected))
        html.append("</select>")

        html.append("<div %s>" % html_params(class_="input-group-append"))
        html.append(
            '<button class="btn btn-outline-secondary" type="button" data-role="clear-location-btn">'
        )
        html.append('<i class="fa fa-times"></i>')
        html.append("</button>")
        html.append(
            '<button class="btn btn-outline-primary" type="button" data-role="geolocation-btn">'
        )
        html.append('<i class="fa fa-location-arrow"></i>')
        html.append("</button>")
        html.append("</div>")

        return Markup("".join(html))


class AjaxValidationWidget(TextInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("data-role", "ajax-validation")
        kwargs.setdefault("data-url", f"{request.base_url}?field_name={field.name}")
        return super().__call__(field, **kwargs)


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


class DateRangeWidget:
    def __call__(self, field, **kwargs):
        html = []
        html.append("<div %s>" % html_params(class_="row mb-1"))

        for subfield in field:
            if subfield.type in ("HiddenField", "CSRFTokenField"):  # pragma: no cover
                continue

            html.append("<div %s>" % html_params(class_="col-sm"))
            html.append("<div %s>" % html_params(class_="input-group"))
            html.append("<div %s>" % html_params(class_="input-group-prepend"))
            html.append(
                "<span %s>%s</span>"
                % (html_params(class_="input-group-text"), str(subfield.label.text))
            )
            html.append("</div>")
            html.append(str(subfield))
            html.append("</div>")
            html.append("</div>")

        html.append("</div>")
        return Markup("".join(html))


class RadiusWidget:
    def __call__(self, field, **kwargs):
        html = []
        html.append("<div %s>" % html_params(class_="row mb-1"))

        # Location
        subfield = field.location
        html.append("<div %s>" % html_params(class_="col-sm-8"))
        html.append("<div %s>" % html_params(class_="input-group"))
        html.append(str(subfield))
        html.append("</div>")
        html.append("</div>")

        # Distance
        subfield = field.distance
        html.append("<div %s>" % html_params(class_="col-sm-4"))
        html.append("<div %s>" % html_params(class_="input-group"))
        html.append("<div %s>" % html_params(class_="input-group-prepend"))
        html.append(
            "<span %s>%s</span>"
            % (html_params(class_="input-group-text"), str(subfield.label.text))
        )
        html.append("</div>")
        html.append(str(subfield))
        html.append("</div>")
        html.append("</div>")

        html.append("</div>")
        html.append(str(field.coordinate))
        html.append(str(field.location_name))
        return Markup("".join(html))
