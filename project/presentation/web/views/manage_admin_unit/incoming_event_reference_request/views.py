from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext

from project.application.commands import (
    RejectEventReferenceRequestCommand,
    VerifyEventReferenceRequestCommand,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.presentation.web.modular.base_views import BaseListView, BaseUpdateView
from project.presentation.web.views.manage_admin_unit.incoming_event_reference_request.forms import (
    ReferenceRequestReviewForm,
)
from project.presentation.web.views.utils import flash_message, handle_base_error


class ListView(BaseListView):
    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "Here you will find requests from other organizations asking you to recommend one of their events.",
        )


class ReviewView(BaseUpdateView):
    form_class = ReferenceRequestReviewForm
    template_file_name = "review.html"

    def get_title(self, **kwargs):
        return lazy_gettext(
            "Review %(model_display_name)s",
            model_display_name=self.handler.get_model_display_name(),
        )

    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.review_status == EventReferenceRequestReviewStatus.verified:
            flash_message(
                gettext("Request already verified"),
                url_for("main.event", event_id=object.event_id),
                gettext("View event"),
                "danger",
            )
            return redirect(self.get_redirect_url())

        return None

    def render_template(self, form, object, **kwargs):
        request = object
        auto_verify = request.auto_verify

        if not auto_verify:
            form.auto_verify.description = gettext(
                "If all upcoming reference requests of %(admin_unit_name)s should be verified automatically.",
                admin_unit_name=request.admin_unit.name,
            )

        dates = request.upcoming_dates

        return super().render_template(form=form, object=object, dates=dates, **kwargs)

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        actor = self.app_context_provider.get_current_actor()
        auto_verify = form.auto_verify.data

        if form.review_status.data == EventReferenceRequestReviewStatus.verified:
            cmd = VerifyEventReferenceRequestCommand(
                actor=actor,
                id=object.id,
                rating=form.rating.data,
                auto_verify=auto_verify,
            )
            self.message_bus.handle_command(cmd)
            success_text = gettext("Reference successfully created")
        else:
            rejection_reason = (
                form.rejection_reason.data if form.rejection_reason.data else None
            )
            cmd = RejectEventReferenceRequestCommand(
                actor=actor,
                id=object.id,
                rejection_reason=rejection_reason,
                auto_verify=auto_verify,
            )
            self.message_bus.handle_command(cmd)
            success_text = gettext("Request successfully updated")

        flash(success_text, "success")
        return redirect(self.get_redirect_url(object=object))

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)
