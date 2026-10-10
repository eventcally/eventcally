from project.domain.translation import dummy_gettext

from .base_error import BaseError


class UnauthorizedError(BaseError):
    default_message = dummy_gettext("Actor is not authorized to perform this action.")
