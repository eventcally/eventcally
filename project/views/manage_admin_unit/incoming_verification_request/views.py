from typing import Annotated

from dependency_injector.wiring import Provide
from flask import redirect, url_for
from flask_babel import gettext, lazy_gettext

from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequestReviewStatus,
)
from project.modular.base_views import BaseUpdateView
from project.services.organization_service import OrganizationService
from project.services.organization_verification_request_service import (
    OrganizationVerificationRequestService,
)
from project.views.manage_admin_unit.incoming_verification_request.forms import (
    VerificationRequestReviewForm,
)
from project.views.utils import flash_message


class ReviewView(BaseUpdateView):
    organization_service: Annotated[
        OrganizationService, Provide["services.organization_service"]
    ]
    organization_verification_request_service: Annotated[
        OrganizationVerificationRequestService,
        Provide["services.organization_verification_request_service"],
    ]
    form_class = VerificationRequestReviewForm
    template_file_name = "review.html"

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Review %(model_display_name)s",
            model_display_name=self.model.get_display_name(),
        )

    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.review_status == AdminUnitVerificationRequestReviewStatus.verified:
            flash_message(
                gettext("Verification request already verified"),
                url_for("organizations", path=object.source_admin_unit_id),
                gettext("View organization"),
                "danger",
            )
            return redirect(self.get_redirect_url())

        return None

    def render_template(self, form, object, **kwargs):
        form.auto_verify.description = gettext(
            "If all upcoming reference requests of %(admin_unit_name)s should be verified automatically.",
            admin_unit_name=object.source_admin_unit.name,
        )

        return super().render_template(form=form, object=object, **kwargs)

    def save_object(self, object, form):
        if object.review_status == AdminUnitVerificationRequestReviewStatus.verified:
            self.organization_service.verify_incoming_organization_verification_request(
                object, form.auto_verify.data if form.auto_verify.data else None
            )
        else:
            self.organization_verification_request_service.update_object(object)

    def get_success_text(self, object, form):
        if object.review_status == AdminUnitVerificationRequestReviewStatus.verified:
            return gettext("Organization successfully verified")

        return gettext("Verification request successfully updated")

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)
