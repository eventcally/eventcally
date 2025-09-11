from typing import OrderedDict

from markupsafe import Markup

from project.models.trackable_mixin import TrackableMixin


class BaseDisplay:
    main_index = 0

    def __init_subclass__(cls):
        props = []
        for name in dir(cls):
            if not name.startswith("_"):
                prop = getattr(cls, name)
                if hasattr(prop, "_is_prop"):
                    props.append((name, prop))

        props.sort(key=lambda x: (x[1].creation_counter, x[0]))
        cls._unbound_props = props

    def __init__(self):
        self._props = OrderedDict()

        for name, unbound_prop in self._unbound_props:
            prop = unbound_prop.bind(self, name=name)
            self._props[name] = prop

        for name, prop in self._props.items():
            # Set all the props to attributes so that they obscure the class
            # attributes with the same names.
            setattr(self, name, prop)

    def get_ordered_props(self):
        return self._props.values()

    def get_prop_label(self, prop):
        return prop.label

    def get_prop_header(self, prop):
        return (
            Markup(
                f'<i class="fa-fw {prop.icon}" data-toggle="tooltip" title="{prop.label}" data-boundary="window"></i>'
            )
            if prop.icon
            else self.get_prop_label(prop)
        )

    def should_display_prop(self, prop, object):
        return prop.should_display(object)

    def get_prop_display_value(self, prop, object):
        return prop.get_display_value(object)

    def get_prop_link(self, prop, object):
        return prop.get_link(object)

    def should_show_audit(self, object):
        return isinstance(object, TrackableMixin) and object.created_at is not None

    def should_audit_show_user(self, object):
        return self.should_show_audit(object)
