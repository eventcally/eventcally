from project.domain.translation import dummy_gettext

from .base_error import BaseError


class NotFoundError(BaseError):
    default_message = dummy_gettext("The requested resource was not found")
