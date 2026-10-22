from project.domain.translation import dummy_gettext

from .base_error import BaseError


class ExternalCalendarError(BaseError):
    default_message = dummy_gettext("The external calendar could not be loaded.")
