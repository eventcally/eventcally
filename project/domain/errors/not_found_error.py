from .base_error import BaseError


class NotFoundError(BaseError):
    default_message = "The requested resource was not found"
