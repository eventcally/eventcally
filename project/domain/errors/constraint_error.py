from .base_error import BaseError


class ConstraintError(BaseError):
    default_message = "Action violates database constraint."
