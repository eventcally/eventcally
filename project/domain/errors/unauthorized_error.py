from .base_error import BaseError


class UnauthorizedError(BaseError):
    default_message = "Actor is not authorized to perform this action."
