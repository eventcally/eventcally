from flask import redirect, render_template, url_for
from flask_babel import gettext, lazy_gettext

from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.presentation.web.boot import build_boot_data
from project.presentation.web.modular.base_views import BaseUpdateView
from project.presentation.web.views.utils import flash_message


def _render_shell(title):
    return render_template(
        "manage/request_review.html",
        entry="manage",
        title=title,
        boot=build_boot_data(base="/"),
    )


class ReviewView(BaseUpdateView):
    """A shell: the Vue page reads and decides through `/bff/manage`."""

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Review %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )

    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.review_status == OrganizationVerificationRequestReviewStatus.verified:
            flash_message(
                gettext("Verification request already verified"),
                url_for("main.organization", id=object.source_admin_unit_id),
                gettext("View organization"),
                "danger",
            )
            return redirect(self.get_redirect_url())

        return None

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        object = self.get_object_from_kwargs(**kwargs)
        response = self.check_object_access(object)

        if response:
            return response

        return _render_shell(self.get_title())

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)
