import os
import pathlib
from functools import reduce

import requests
from flask_babel import lazy_gettext
from flask_sqlalchemy.model import camel_to_snake_case
from psycopg2.errorcodes import CHECK_VIOLATION, UNIQUE_VIOLATION
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.base import NO_CHANGE, object_state


def dummy_gettext(message: str):
    return message


def strings_are_equal_ignoring_case(string1: str, string2: str):
    return string1 and string2 and string1.casefold() == string2.casefold()


def get_event_category_name(category):
    return lazy_gettext("Event_" + category.name)


def get_localized_enum_name(enum):
    return lazy_gettext(enum.__class__.__name__ + "." + enum.name)


def get_localized_scope(scope: str) -> str:
    loc_key = "Scope_" + scope
    return lazy_gettext(loc_key)


def get_location_str(location) -> str:
    if not location:
        return ""

    if location.street and not location.street.isspace():
        return f"{location.street}, {location.postalCode} {location.city}"

    if location.postalCode or location.city:
        return f"{location.postalCode} {location.city}".strip()

    return ""


def get_place_str(place) -> str:
    if not place:
        return ""

    if place.location:
        return f"{place.name}, {get_location_str(place.location)}"

    return place.name


def make_dir(path):
    try:
        original_umask = os.umask(0)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    finally:
        os.umask(original_umask)


def clear_files_in_dir(path):
    if not os.path.exists(path):  # pragma: no cover
        return

    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file() or entry.is_symlink():
                os.remove(entry.path)


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


def make_integrity_error(
    pgcode: str, message: str = "", statement: str = None
) -> IntegrityError:
    class Psycog2Error(object):
        def __init__(self, pgcode, message):
            self.pgcode = pgcode
            self.message = message

    orig = Psycog2Error(pgcode, message)
    return IntegrityError(statement, list(), orig)


def make_check_violation(message: str = None, statement: str = "") -> IntegrityError:
    return make_integrity_error(CHECK_VIOLATION, message, statement)


def make_unique_violation(message: str = None, statement: str = "") -> IntegrityError:
    return make_integrity_error(UNIQUE_VIOLATION, message, statement)


def get_pending_changes(
    instance, include_collections=True, passive=None, include_keys=None
) -> dict:
    result = {}

    state = object_state(instance)

    if not state.modified:  # pragma: no cover
        return result

    dict_ = state.dict

    for attr in state.manager.attributes:
        if (
            (include_keys and attr.key not in include_keys)
            or (not include_collections and hasattr(attr.impl, "get_collection"))
            or not hasattr(attr.impl, "get_history")
        ):  # pragma: no cover
            continue

        (added, unchanged, deleted) = attr.impl.get_history(
            state, dict_, passive=NO_CHANGE
        )

        if added or deleted:
            old_value = deleted[0] if deleted else None
            new_value = added[0] if added else None
            result[attr.key] = [new_value, old_value]

    return result


def decode_response_content(response: requests.Response) -> str:
    try:
        return response.content.decode("UTF-8")
    except Exception:  # pragma: no cover
        return response.content.decode(response.apparent_encoding)


def snake_case_to_human(snake_case):
    result = snake_case.replace("_", " ")
    return result[:1].upper() + result[1:]


def class_name_to_model_name(class_name):
    result = camel_to_snake_case(class_name)

    if result[1] == "_":
        result = result[:1] + result[2:]

    return result


def model_name_to_plural(model_name):
    if model_name.endswith("s"):
        return model_name

    if model_name.endswith("y"):
        return model_name[:-1] + "ies"

    return f"{model_name}s"


def getattr_keypath(obj, keypath, default=None):
    try:
        return reduce(getattr, keypath.split("."), obj)
    except AttributeError:  # pragma: no cover
        return default
