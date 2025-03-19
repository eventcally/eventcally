from wtforms import FormField, SelectFieldBase, SelectMultipleField, ValidationError
from wtforms.utils import unset_value

from project.maputils import find_gmaps_places, get_gmaps_place
from project.modular.widgets import AjaxSelect2Widget, GooglePlaceWidget, RangeWidget


class VirtualFormField(FormField):
    def __init__(
        self, form_class, label=None, validators=None, separator="-", **kwargs
    ):
        kwargs.setdefault("default", dict)
        super().__init__(form_class, label, validators, separator, **kwargs)

    def process(self, formdata, data=unset_value, extra_filters=None):
        return super().process(formdata, data, extra_filters)

    def populate_obj(self, obj, name):
        self.form.populate_obj(obj)


class DateRangeField(FormField):
    widget = RangeWidget()

    def __init__(
        self, form_class=None, label=None, validators=None, separator="_", **kwargs
    ):
        if not form_class:
            from project.modular.base_form import DateRangeForm

            form_class = DateRangeForm
        kwargs.setdefault("default", dict)
        render_kw = kwargs.setdefault("render_kw", dict())
        render_kw.setdefault("group_class", "")
        super().__init__(form_class, label, validators, separator, **kwargs)

    def process(self, formdata, data=unset_value, extra_filters=None):
        return super().process(formdata, data, extra_filters)

    def populate_obj(self, obj, name):  # pragma: no cover
        self.form.populate_obj(obj)


class GooglePlaceField(SelectFieldBase):
    widget = GooglePlaceWidget()

    def __init__(self, label=None, validators=None, location_only=False, **kwargs):
        render_kw = kwargs.setdefault("render_kw", dict())
        render_kw.setdefault("label_hidden", True)
        super().__init__(label, validators, **kwargs)

        self.location_only = location_only

    def get_bff_google_places(self, keyword):
        google_places = find_gmaps_places(keyword) if keyword else list()
        google_places_result = [
            {
                "id": p["place_id"],
                "gmaps_id": p["place_id"],
                "text": p["description"],
                "main_text": p["structured_formatting"]["main_text"],
            }
            for p in google_places
        ]
        return {"results": google_places_result}

    def get_bff_google_place(self, gmaps_id):
        return get_gmaps_place(gmaps_id)


class SelectMultipleTagField(SelectMultipleField):
    def __init__(
        self,
        label=None,
        validators=None,
        coerce=str,
        **kwargs,
    ):
        validate_choice = False
        choices = []
        render_kw = kwargs.setdefault("render_kw", dict())
        render_kw.setdefault("data-role", "select2-tags")
        super().__init__(label, validators, coerce, choices, validate_choice, **kwargs)

    def process_data(self, value):
        super().process_data(value)

        if self.data:
            self.data = sorted(self.data)
            self.choices = self.data


class AjaxSelectField(SelectFieldBase):
    """
    Ajax Model Select Field
    """

    widget = AjaxSelect2Widget()

    separator = ","

    def __init__(
        self,
        loader,
        label=None,
        validators=None,
        allow_blank=False,
        blank_text="",
        **kwargs,
    ):
        super(AjaxSelectField, self).__init__(label, validators, **kwargs)
        self.loader = loader

        self.allow_blank = allow_blank
        self.blank_text = blank_text

    def _get_data(self):
        if self._formdata:
            model = self.loader.get_one(self._formdata)

            if model is not None:
                self._set_data(model)

        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def process_formdata(self, valuelist):
        if valuelist:
            if self.allow_blank and valuelist[0] == "__None":  # pragma: no cover
                self.data = None
            else:
                self._data = None
                self._formdata = valuelist[0]

    def pre_validate(self, form):
        if not self.allow_blank and self.data is None:  # pragma: no cover
            raise ValidationError(self.gettext("Not a valid choice"))
