from wtforms import SelectFieldBase, ValidationError

from project.presentation.web.modular.widgets import AjaxSelect2Widget


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

    def iter_choices(self):
        choices = []

        if self.data:
            formatted = self.loader.format(self.data)
            choices.append((formatted[0], formatted[1], True, {}))

        return choices

    def process_formdata(self, valuelist):
        if valuelist:
            if self.allow_blank and valuelist[0] == "__None":  # pragma: no cover
                self.data = None
            else:
                self._data = None
                self._formdata = valuelist[0]
        elif self.allow_blank:
            self.data = None

    def pre_validate(self, form):
        if not self.allow_blank and self.data is None:  # pragma: no cover
            raise ValidationError(self.gettext("Not a valid choice"))


class AjaxSelectMultipleField(AjaxSelectField):
    """
    Ajax-enabled model multi-select field.
    """

    widget = AjaxSelect2Widget(multiple=True)

    def __init__(self, loader, label=None, validators=None, default=None, **kwargs):
        if default is None:
            default = []

        super(AjaxSelectMultipleField, self).__init__(
            loader, label, validators, default=default, **kwargs
        )
        self._invalid_formdata = False

    def _get_data(self):
        formdata = self._formdata
        if formdata is not None:
            data = []

            for item in formdata:
                model = self.loader.get_one(item) if item else None

                if model:
                    data.append(model)
                else:  # pragma: no cover
                    self._invalid_formdata = True

            self._set_data(data)

        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def iter_choices(self):
        choices = []

        if self.data:
            for item in self.data:
                formatted = self.loader.format(item)
                choices.append((formatted[0], formatted[1], True, {}))

        return choices

    def process_formdata(self, valuelist):
        self._formdata = set()

        for field in valuelist:
            for n in field.split(self.separator):
                self._formdata.add(n)

    def pre_validate(self, form):
        if self._invalid_formdata:  # pragma: no cover
            raise ValidationError(self.gettext("Not a valid choice"))

    def get_data_ids(self):
        data = self.data
        return [c.id for c in data] if data else []
