from flask import abort, flash, redirect, render_template, url_for
from flask_babelex import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import access_or_401, has_access, has_admin_unit_member_permission
from project.dateutils import get_today
from project.forms.reference_request import ReferenceRequestReviewForm
from project.models import (
    AdminUnitMember,
    EventDate,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
    User,
)
from project.services.reference import create_event_reference_for_request
from project.views.utils import flash_errors, handleSqlError, send_mail


@app.route("/reference_request/<int:id>/review", methods=("GET", "POST"))
@auth_required()
def event_reference_request_review(id):
    request = EventReferenceRequest.query.get_or_404(id)
    access_or_401(request.admin_unit, "reference_request:verify")

    if request.review_status == EventReferenceRequestReviewStatus.verified:
        flash(gettext("Request already verified"), "danger")
        return redirect(
            url_for(
                "manage_admin_unit_reference_requests_incoming",
                id=request.admin_unit_id,
            )
        )

    form = ReferenceRequestReviewForm(obj=request)

    if form.validate_on_submit():
        form.populate_obj(request)

        if request.review_status != EventReferenceRequestReviewStatus.rejected:
            request.rejection_reason = None

        if request.rejection_reason == 0:
            request.rejection_reason = None

        try:
            if request.review_status == EventReferenceRequestReviewStatus.verified:
                reference = create_event_reference_for_request(request)
                reference.rating = form.rating.data
                msg = gettext("Reference successfully created")
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
    members = (
        AdminUnitMember.query.join(User)
        .filter(AdminUnitMember.admin_unit_id == request.event.admin_unit_id)
        .all()
    )

    for member in members:
        if has_admin_unit_member_permission(member, "reference_request:create"):
            send_mail(
                member.user.email,
                gettext("Event review status updated"),
                "reference_request_review_status_notice",
                request=request,
            )
