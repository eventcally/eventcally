from flask import abort, flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import (
    access_or_401,
    get_admin_unit_members_with_permission,
    has_access,
)
from project.dateutils import get_today
from project.forms.reference_request import ReferenceRequestReviewForm
from project.models import (
    EventDate,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from project.services.admin_unit import (
    get_admin_unit_relation,
    upsert_admin_unit_relation,
)
from project.services.reference import create_event_reference_for_request
from project.views.utils import (
    flash_errors,
    flash_message,
    handleSqlError,
    send_mails_async,
)


@app.route("/reference_request/<int:id>/review", methods=("GET", "POST"))
@auth_required()
def event_reference_request_review(id):
    request = EventReferenceRequest.query.get_or_404(id)
    access_or_401(request.admin_unit, "reference_request:verify")

    if request.review_status == EventReferenceRequestReviewStatus.verified:
        flash_message(
            gettext("Request already verified"),
            url_for("event", event_id=request.event_id),
            gettext("View event"),
            "danger",
        )
        return redirect(
            url_for(
                "manage_admin_unit_reference_requests_incoming",
                id=request.admin_unit_id,
            )
        )

    form = ReferenceRequestReviewForm(obj=request)

    if form.validate_on_submit():
        form.populate_obj(request)

        try:
            if request.review_status == EventReferenceRequestReviewStatus.verified:
                reference = create_event_reference_for_request(request)
                reference.rating = form.rating.data
                msg = gettext("Reference successfully created")

                if form.auto_verify.data:
                    relation = upsert_admin_unit_relation(
                        request.admin_unit_id, request.event.admin_unit_id
                    )
                    relation.auto_verify_event_reference_requests = True
            else:
                msg = gettext("Request successfully updated")

            db.session.commit()
            send_reference_request_review_status_mails(request)
            flash(msg, "success")
            return redirect(
                url_for(
                    "manage_admin_unit_reference_requests_incoming",
                    id=request.admin_unit_id,
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

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
    return render_template(
        "reference_request/review.html",
        form=form,
        auto_verify=auto_verify,
        dates=dates,
        request=request,
        event=request.event,
    )


@app.route("/reference_request/<int:id>/review_status")
def event_reference_request_review_status(id):
    request = EventReferenceRequest.query.get_or_404(id)

    if not has_access(
        request.admin_unit, "reference_request:verify"
    ) and not has_access(request.event.admin_unit, "reference_request:create"):
        abort(401)

    return render_template(
        "reference_request/review_status.html",
        reference_request=request,
        event=request.event,
    )


def send_reference_request_review_status_mails(request):
    # Benachrichtige alle Mitglieder der AdminUnit, die diesen Request erstellt hatte
    members = get_admin_unit_members_with_permission(
        request.event.admin_unit_id, "reference_request:create"
    )
    emails = list(map(lambda member: member.user.email, members))

    send_mails_async(
        emails,
        gettext("Event review status updated"),
        "reference_request_review_status_notice",
        request=request,
    )
