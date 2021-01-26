from flask_babelex import lazy_gettext
import pathlib
import os


def get_event_category_name(category):
    return lazy_gettext("Event_" + category.name)


def get_localized_enum_name(enum):
    return lazy_gettext(enum.__class__.__name__ + "." + enum.name)


def make_dir(path):
    try:
        original_umask = os.umask(0)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    finally:
        os.umask(original_umask)
