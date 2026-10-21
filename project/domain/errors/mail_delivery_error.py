from project.domain.translation import dummy_gettext

from .base_error import BaseError


class MailDeliveryError(BaseError):
    default_message = dummy_gettext("The mail could not be sent.")
