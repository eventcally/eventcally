from project.domain.translation import dummy_gettext

from .base_error import BaseError


class ConstraintError(BaseError):
    default_message = dummy_gettext("Action violates database constraint.")
