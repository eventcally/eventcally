from flask import redirect, url_for
from flask_babel import gettext, lazy_gettext

from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequestReviewStatus,
)
from project.modular.base_views import BaseUpdateView
from project.services.admin_unit import upsert_admin_unit_relation
from project.views.manage_admin_unit.incoming_verification_request.forms import (
    VerificationRequestReviewForm,
)
from project.views.utils import flash_message
from project.views.verification_request_review import (
    send_verification_request_review_status_mails,
)


class ReviewView(BaseUpdateView):
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

    def complete_object(self, object, form):
        super().complete_object(object, form)

        if object.review_status == AdminUnitVerificationRequestReviewStatus.verified:
            relation = upsert_admin_unit_relation(
                object.target_admin_unit_id, object.source_admin_unit_id
            )
            relation.verify = True

            if form.auto_verify.data:
                relation.auto_verify_event_reference_requests = True

    def after_commit(self, object, form):
        send_verification_request_review_status_mails(object)

    def get_success_text(self, object, form):
        if object.review_status == AdminUnitVerificationRequestReviewStatus.verified:
            return gettext("Organization successfully verified")

        return gettext("Verification request successfully updated")

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)
