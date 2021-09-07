from flask import flash, redirect, render_template, url_for
from flask_babelex import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import desc

from project import app, db
from project.access import (
    access_or_401,
    get_admin_unit_for_manage_or_404,
    get_admin_unit_members_with_permission,
    get_admin_units_for_event_reference_request,
)
from project.forms.reference_request import CreateEventReferenceRequestForm
from project.models import (
    Event,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from project.services.admin_unit import get_admin_unit_relation
from project.services.reference import (
    create_event_reference_for_request,
    get_reference_requests_incoming_query,
)
from project.views.utils import (
    flash_errors,
    get_pagination_urls,
    handleSqlError,
    send_mails,
)


@app.route("/manage/admin_unit/<int:id>/reference_requests/incoming")
@auth_required()
def manage_admin_unit_reference_requests_incoming(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    requests = (
        get_reference_requests_incoming_query(admin_unit)
        .order_by(desc(EventReferenceRequest.created_at))
        .paginate()
    )

    return render_template(
        "manage/reference_requests_incoming.html",
        admin_unit=admin_unit,
        requests=requests.items,
        pagination=get_pagination_urls(requests, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/reference_requests/outgoing")
@auth_required()
def manage_admin_unit_reference_requests_outgoing(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    requests = (
        EventReferenceRequest.query.join(Event)
        .filter(Event.admin_unit_id == admin_unit.id)
        .order_by(desc(EventReferenceRequest.created_at))
        .paginate()
    )

    return render_template(
        "manage/reference_requests_outgoing.html",
        admin_unit=admin_unit,
        requests=requests.items,
        pagination=get_pagination_urls(requests, id=id),
    )


@app.route("/event/<int:event_id>/reference_request/create", methods=("GET", "POST"))
@auth_required()
def event_reference_request_create(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, "reference_request:create")

    form = CreateEventReferenceRequestForm()
    form.admin_unit_id.choices = sorted(
        [
            (admin_unit.id, admin_unit.name)
            for admin_unit in get_admin_units_for_event_reference_request(event)
        ],
        key=lambda admin_unit: admin_unit[1],
    )

    if form.validate_on_submit():
        request = EventReferenceRequest()
        form.populate_obj(request)
        request.event = event

        try:
            db.session.add(request)

            relation = get_admin_unit_relation(
                request.admin_unit_id, event.admin_unit_id
            )
            auto_verify = relation and relation.auto_verify_event_reference_requests

            if auto_verify:
                request.review_status = EventReferenceRequestReviewStatus.verified
                reference = create_event_reference_for_request(request)
                send_auto_reference_inbox_mails(reference)
                msg = gettext("Reference successfully created")
            else:
                request.review_status = EventReferenceRequestReviewStatus.inbox
                send_reference_request_inbox_mails(request)
                msg = gettext(
                    "Request successfully created. You will be notified after the other organization reviews the event."
                )

            db.session.commit()
            flash(msg, "success")
            return redirect(
                url_for(
                    "manage_admin_unit_reference_requests_outgoing",
                    id=event.admin_unit_id,
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("event/reference_request.html", form=form, event=event)


def send_member_reference_request_verify_mails(
    admin_unit_id, subject, template, **context
):
    # Benachrichtige alle Mitglieder der AdminUnit, die Requests verifizieren können
    members = get_admin_unit_members_with_permission(
        admin_unit_id, "reference_request:verify"
    )
    emails = list(map(lambda member: member.user.email, members))

    send_mails(emails, subject, template, **context)


def send_reference_request_inbox_mails(request):
    send_member_reference_request_verify_mails(
        request.admin_unit_id,
        gettext("New reference request"),
        "reference_request_notice",
        request=request,
    )


def send_auto_reference_inbox_mails(reference):
    send_member_reference_request_verify_mails(
        reference.admin_unit_id,
        gettext("New reference automatically verified"),
        "reference_auto_verified_notice",
        reference=reference,
    )
