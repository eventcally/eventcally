from project.domain.translation import dummy_gettext

from .base_error import BaseError


class DuplicateError(BaseError):
    default_message = dummy_gettext(
        "An entry with the entered values already exists. Duplicate entries are not allowed."
    )
