from .base_error import BaseError


class DuplicateError(BaseError):
    default_message = "An entry with the entered values already exists. Duplicate entries are not allowed."
