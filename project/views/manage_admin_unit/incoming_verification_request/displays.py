from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BaseProp, DateProp, EnumProp
from project.views.manage_admin_unit.outgoing_verification_request.displays import (
    AdminUnitVerificationRequestReviewStatusPropFormatter,
)


class ListDisplay(BaseDisplay):
    source_admin_unit = BaseProp(lazy_gettext("Organization"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=AdminUnitVerificationRequestReviewStatusPropFormatter(),
    )
    created_at = DateProp(lazy_gettext("Created at"))
