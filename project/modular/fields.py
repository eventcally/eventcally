from wtforms import SelectFieldBase, ValidationError

from project.modular.widgets import AjaxSelect2Widget


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
        **kwargs
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
