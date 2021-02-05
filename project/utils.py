from flask_babelex import lazy_gettext
import pathlib
import os


def get_event_category_name(category):
    return lazy_gettext("Event_" + category.name)


def get_localized_enum_name(enum):
    return lazy_gettext(enum.__class__.__name__ + "." + enum.name)


def get_localized_scope(scope: str) -> str:
    type_name, action = scope.split(":")
    loc_lazy_gettext = lazy_gettext(type_name.capitalize())
    loc_action = lazy_gettext(action)
    return f"{loc_lazy_gettext} ({loc_action})"


def make_dir(path):
    try:
        original_umask = os.umask(0)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    finally:
        os.umask(original_umask)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]
