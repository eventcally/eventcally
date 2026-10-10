from project.domain.translation import dummy_gettext

from .base_error import BaseError


class InfrastructureError(BaseError):
    default_message = dummy_gettext("An infrastructure error occurred.")
