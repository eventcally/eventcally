from flask import redirect, url_for
from flask_babel import gettext, lazy_gettext

from project.dateutils import get_today
from project.models.event_date import EventDate
from project.models.event_reference_request import EventReferenceRequestReviewStatus
from project.modular.base_views import BaseListView, BaseUpdateView
from project.services.admin_unit import (
    get_admin_unit_relation,
    upsert_admin_unit_relation,
)
from project.services.reference import create_event_reference_for_request
from project.views.manage_admin_unit.incoming_event_reference_request.forms import (
    ReferenceRequestReviewForm,
)
from project.views.reference_request_review import (
    send_reference_request_review_status_mails,
)
from project.views.utils import flash_message


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
            model_display_name=self.model.get_display_name(),
        )

    def check_object_access(self, object):
        result = super().check_object_access(object)
        if result:  # pragma: no cover
            return result

        if object.review_status == EventReferenceRequestReviewStatus.verified:
            flash_message(
                gettext("Request already verified"),
                url_for("event", event_id=object.event_id),
                gettext("View event"),
                "danger",
            )
            return redirect(self.get_redirect_url())

        return None

    def render_template(self, form, object, **kwargs):
        request = object
        relation = get_admin_unit_relation(
            request.admin_unit_id, request.event.admin_unit_id
        )
        auto_verify = relation and relation.auto_verify_event_reference_requests

        if not auto_verify:
            form.auto_verify.description = gettext(
                "If all upcoming reference requests of %(admin_unit_name)s should be verified automatically.",
                admin_unit_name=request.admin_unit.name,
            )

        today = get_today()
        dates = (
            EventDate.query.with_parent(request.event)
            .filter(EventDate.start >= today)
            .order_by(EventDate.start)
            .all()
        )

        return super().render_template(form=form, object=object, dates=dates, **kwargs)

    def complete_object(self, object, form):
        super().complete_object(object, form)

        if object.review_status == EventReferenceRequestReviewStatus.verified:
            reference = create_event_reference_for_request(object)
            reference.rating = form.rating.data

            if form.auto_verify.data:
                relation = upsert_admin_unit_relation(
                    object.admin_unit_id, object.event.admin_unit_id
                )
                relation.auto_verify_event_reference_requests = True

    def after_commit(self, object, form):
        send_reference_request_review_status_mails(object)

    def get_success_text(self, object, form):
        if object.review_status == EventReferenceRequestReviewStatus.verified:
            return gettext("Reference successfully created")

        return gettext("Request successfully updated")

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)
