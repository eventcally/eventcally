from flask import abort, flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import (
    can_request_event_reference,
    get_admin_unit_for_manage_or_404,
    get_admin_unit_members_with_permission,
)
from project.forms.reference_request import CreateEventReferenceRequestForm
from project.models import (
    Event,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from project.models.event_reference import EventReference
from project.services.admin_unit import (
    get_admin_unit_by_id,
    get_admin_unit_relation,
    get_admin_unit_suggestions_for_reference_requests,
)
from project.services.reference import (
    create_event_reference_for_request,
    get_reference_requests_incoming_query,
    get_reference_requests_outgoing_query,
)
from project.services.search_params import EventReferenceRequestSearchParams
from project.views.utils import (
    flash_errors,
    get_pagination_urls,
    handleSqlError,
    send_mails_async,
)


@app.route("/manage/admin_unit/<int:id>/reference_requests/incoming")
@auth_required()
def manage_admin_unit_reference_requests_incoming(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    params = EventReferenceRequestSearchParams()
    params.admin_unit_id = admin_unit.id
    requests = get_reference_requests_incoming_query(params).paginate()

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

    params = EventReferenceRequestSearchParams()
    params.admin_unit_id = admin_unit.id
    requests = get_reference_requests_outgoing_query(params).paginate()

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

    if not can_request_event_reference(event):
        abort(401)

    form = CreateEventReferenceRequestForm()

    if form.admin_unit_id.data and form.admin_unit_id.data > 0:
        admin_unit = get_admin_unit_by_id(form.admin_unit_id.data)

        if admin_unit:
            form.admin_unit_id.choices = [(admin_unit.id, admin_unit.name)]

    if not form.admin_unit_id.choices:
        (
            admin_unit_choices,
            selected_ids,
        ) = get_admin_unit_suggestions_for_reference_requests(
            event.admin_unit, max_choices=1
        )
        form.admin_unit_id.choices = [(a.id, a.name) for a in admin_unit_choices]
        form.admin_unit_id.data = (
            admin_unit_choices[0].id if len(admin_unit_choices) > 0 else None
        )

    if form.validate_on_submit():
        reference_request = EventReferenceRequest()
        form.populate_obj(reference_request)
        reference_request.event = event

        try:
            db.session.add(reference_request)

            reference, msg = handle_request_according_to_relation(
                reference_request, event
            )
            db.session.commit()
            send_reference_request_mails(reference_request, reference)
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


def handle_request_according_to_relation(
    request: EventReferenceRequest, event: Event
) -> str:
    admin_unit = (
        request.admin_unit
        if request.admin_unit
        else get_admin_unit_by_id(request.admin_unit_id)
    )
    relation = get_admin_unit_relation(admin_unit.id, event.admin_unit_id)
    auto_verify = relation and relation.auto_verify_event_reference_requests
    reference = None

    if auto_verify:
        request.review_status = EventReferenceRequestReviewStatus.verified
        reference = create_event_reference_for_request(request)

        msg = gettext(
            "%(organization)s accepted your reference request",
            organization=admin_unit.name,
        )
    else:
        request.review_status = EventReferenceRequestReviewStatus.inbox

        msg = gettext(
            "Reference request to %(organization)s successfully created. You will be notified after the other organization reviews the event.",
            organization=admin_unit.name,
        )

    return reference, msg


def send_reference_request_mails(
    request: EventReferenceRequest, reference: EventReference
):
    if reference:
        _send_auto_reference_mails(reference)
    else:
        _send_reference_request_inbox_mails(request)


def _send_reference_request_inbox_mails(request):
    _send_member_reference_request_verify_mails(
        request.admin_unit_id,
        gettext("New reference request"),
        "reference_request_notice",
        request=request,
    )


def _send_auto_reference_mails(reference):
    _send_member_reference_request_verify_mails(
        reference.admin_unit_id,
        gettext("New reference automatically verified"),
        "reference_auto_verified_notice",
        reference=reference,
    )


def _send_member_reference_request_verify_mails(
    admin_unit_id, subject, template, **context
):
    # Benachrichtige alle Mitglieder der AdminUnit, die Requests verifizieren können
    members = get_admin_unit_members_with_permission(
        admin_unit_id, "reference_request:verify"
    )
    emails = list(map(lambda member: member.user.email, members))

    send_mails_async(emails, subject, template, **context)
