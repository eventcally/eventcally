import urllib.parse
from werkzeug.datastructures import MultiDict


# see https://www.w3.org/TR/html52/sec-forms.html
class Form:
    def __init__(self, form):
        assert form.name == "form"  # feed me BeautifulSoup <form> tags

        self.form = form
        self._action = form.get("action", "")
        self._method = form.get("method", "GET")

        self.fields = MultiDict()
        self.buttons = {}

        for field in form.find_all(("input", "button", "select", "textarea")):
            name = field.get("name")
            if not name:
                continue

            field_value = field.get("value")

            if field.name == "select":
                options = field.find_all("option")
                selected_values = list()

                for option in options:
                    if option.has_attr("selected"):
                        selected_values.append(option.get("value"))

                if len(selected_values) == 0 and len(options) > 0:
                    selected_values.append(options[0].get("value"))

                if field.has_attr("multiple"):
                    field_value = selected_values
                elif len(selected_values) > 0:
                    field_value = selected_values[0]

            self.fields.add(name, (field, field_value))

            if field.name in ("input", "button"):
                if field.get("type") == "submit":
                    self.buttons[name] = (
                        field.get("formaction"),
                        field.get("formmethod"),
                    )

    def _get_default_button(self):
        if self.buttons:
            return next(iter(self.buttons.keys()))

    def get_action(self, button=None, relative_to=""):
        # Get default submit button if none specified
        if button is None:
            button = self._get_default_button()

        # Use the submit button's formaction if available
        action = None if button is None else self.buttons[button][0]
        action = action or self._action
        return urllib.parse.urljoin(relative_to, action)

    def get_method(self, button=None):
        if button is None:
            button = self._get_default_button()

        method = None if button is None else self.buttons[button][1]
        return method or self._method

    def _fill_impl(self, button, values):
        filled = MultiDict()

        for form_name, (field, default_value) in self.fields.items(multi=True):
            # Skip disabled fields
            if field.has_attr("disabled"):
                continue

            # Skip buttons that are not the submit button
            is_button = (field.name == "button") or (
                field.name == "input"
                and field.get("type") in ("submit", "image", "reset", "button")
            )
            if is_button and form_name != button:
                continue

            # Skip radio buttons and checkboxes that are not checked
            is_radio_or_checkbox = field.name == "input" and field.get("type") in (
                "radio",
                "checkbox",
            )
            if is_radio_or_checkbox and not field.has_attr("checked"):
                continue

            # Add the default value
            if default_value is None:
                if is_button:
                    default_value = "Submit"
                elif is_radio_or_checkbox:
                    default_value = "on"
                else:
                    default_value = ""

            if type(default_value) is list:
                filled.setlist(form_name, default_value)
            else:
                filled.add(form_name, default_value)

        # Override any form values with our input
        for key, value in values.items():
            filled.pop(key)
            if type(value) is list:
                filled.setlist(key, value)
            else:
                filled.add(key, value)
        return filled

    def fill(self, *args):
        if len(args) == 0:
            return self._fill_impl(self._get_default_button(), {})
        elif len(args) == 1:
            return self._fill_impl(self._get_default_button(), args[0])
        elif len(args) == 2:
            return self._fill_impl(args[0], args[1])
        raise ValueError("Expected fill(values) or fill(button, values)")
