from datetime import datetime

from flask import Response, flash, jsonify, redirect, render_template, request, url_for
from flask_babel import gettext
from flask_security import auth_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import (
    access_or_401,
    can_read_event_or_401,
    can_reference_event,
    can_request_event_reference,
    can_request_event_reference_from_admin_unit,
    get_admin_unit_members_with_permission,
    has_access,
)
from project.dateutils import create_icalendar, get_next_full_hour
from project.forms.event import CreateEventForm, DeleteEventForm, UpdateEventForm
from project.jsonld import get_sd_for_event_date
from project.models import (
    AdminUnit,
    Event,
    EventCategory,
    EventOrganizer,
    EventPlace,
    EventReference,
    EventReviewStatus,
    EventSuggestion,
    PublicStatus,
)
from project.models.event_reference_request import EventReferenceRequest
from project.services.admin_unit import (
    get_admin_unit_suggestions_for_reference_requests,
)
from project.services.event import (
    create_ical_events_for_event,
    get_event_with_details_or_404,
    get_meta_data,
    get_significant_event_changes,
    get_upcoming_event_dates,
    insert_event,
    update_event,
    upsert_event_category,
)
from project.utils import get_event_category_name
from project.views.event_suggestion import send_event_suggestion_review_status_mail
from project.views.reference_request import (
    handle_request_according_to_relation,
    send_reference_request_mails,
)
from project.views.utils import (
    flash_errors,
    flash_message,
    get_calendar_links_for_event,
    get_share_links,
    handleSqlError,
    send_template_mails_to_admin_unit_members_async,
    send_template_mails_to_users_async,
    set_current_admin_unit,
)


@app.route("/event/<int:event_id>")
def event(event_id):
    event = get_event_with_details_or_404(event_id)
    can_read_event_or_401(event)
    user_rights = get_user_rights(event)
    dates = get_upcoming_event_dates(event.id)
    url = url_for("event", event_id=event_id, _external=True)
    share_links = get_share_links(url, event.name)
    calendar_links = get_calendar_links_for_event(event)

    structured_datas = list()
    for event_date in dates:
        structured_data = app.json.dumps(get_sd_for_event_date(event_date), indent=2)
        structured_datas.append(structured_data)

    return render_template(
        "event/read.html",
        event=event,
        dates=dates,
        structured_datas=structured_datas,
        meta=get_meta_data(event),
        user_rights=user_rights,
        canonical_url=url_for("event", event_id=event_id, _external=True),
        share_links=share_links,
        calendar_links=calendar_links,
    )


@app.route("/event/<int:event_id>/actions")
def event_actions(event_id):
    event = Event.query.get_or_404(event_id)
    can_read_event_or_401(event)
    user_rights = get_user_rights(event)
    url = url_for("event", event_id=event_id, _external=True)
    share_links = get_share_links(url, event.name)

    return render_template(
        "event/actions.html",
        event=event,
        user_rights=user_rights,
        share_links=share_links,
    )


@app.route("/event/<int:event_id>/report")
def event_report(event_id):
    event = Event.query.get_or_404(event_id)
    can_read_event_or_401(event)

    return render_template("event/report.html")


def prepare_form_reference_requests(form, admin_unit):
    if not can_request_event_reference_from_admin_unit(admin_unit):
        form.reference_request_admin_unit_id.choices = []
        return

    (
        admin_unit_choices,
        selected_ids,
    ) = get_admin_unit_suggestions_for_reference_requests(admin_unit)

    form.reference_request_admin_unit_id.choices = sorted(
        [(a.id, a.name) for a in admin_unit_choices],
        key=lambda a: a[1],
    )

    if not form.is_submitted():
        form.reference_request_admin_unit_id.data = selected_ids


@app.route("/admin_unit/<int:id>/events/create", methods=("GET", "POST"))
@auth_required()
def event_create_for_admin_unit_id(id):
    admin_unit = AdminUnit.query.get_or_404(id)
    access_or_401(admin_unit, "event:create")
    set_current_admin_unit(admin_unit)

    form = CreateEventForm(
        admin_unit_id=admin_unit.id, category_ids=[upsert_event_category("Other").id]
    )
    prepare_event_form(form)
    prepare_form_reference_requests(form, admin_unit)

    # Vorlagen
    event_suggestion = None
    event_template = None

    event_template_id = (
        int(request.args.get("template_id")) if "template_id" in request.args else 0
    )
    if event_template_id > 0:
        event_template = Event.query.get_or_404(event_template_id)
        if not form.is_submitted():
            form.process(obj=event_template)
            form.category_ids.data = [c.id for c in event_template.categories]
            prepare_organizer(form)
            prepare_event_place(form)

    if not event_template:
        event_suggestion_id = (
            int(request.args.get("event_suggestion_id"))
            if "event_suggestion_id" in request.args
            else 0
        )

        if event_suggestion_id > 0:
            event_suggestion = EventSuggestion.query.get_or_404(event_suggestion_id)
            access_or_401(event_suggestion.admin_unit, "event:verify")

            if event_suggestion.verified and event_suggestion.event_id:
                return redirect(
                    url_for(
                        "event_suggestion_review_status",
                        event_suggestion_id=event_suggestion.id,
                    )
                )

            prepare_event_form_for_suggestion(form, event_suggestion)
            if form.is_submitted():
                form.process(request.form)
                prepare_date_definition(form)

    if form.validate_on_submit():
        event = Event()
        update_event_with_form(event, form, event_suggestion)
        event.admin_unit_id = admin_unit.id

        if form.event_place_choice.data == 2:
            event.event_place.admin_unit_id = event.admin_unit_id

        if form.organizer_choice.data == 2:
            event.organizer.admin_unit_id = event.admin_unit_id

        try:
            if event_suggestion:
                event_suggestion.event = event
                event_suggestion.review_status = EventReviewStatus.verified
                event_suggestion.rejection_resaon = None

            insert_event(event)
            db.session.commit()

            if event_suggestion:
                send_event_suggestion_review_status_mail(event_suggestion)

            success_msg = (
                gettext("Event successfully published")
                if event.public_status == PublicStatus.published
                else gettext("Draft successfully saved")
                if event.public_status == PublicStatus.draft
                else gettext("Event successfully planned")
            )
            flash_message(
                success_msg,
                url_for("event", event_id=event.id),
            )

            if (
                event.public_status == PublicStatus.published
                and form.reference_request_admin_unit_id.data
            ):
                for target_admin_unit_id in form.reference_request_admin_unit_id.data:
                    reference_request = EventReferenceRequest()
                    reference_request.event_id = event.id
                    reference_request.admin_unit_id = target_admin_unit_id
                    db.session.add(reference_request)
                    reference, msg = handle_request_according_to_relation(
                        reference_request, event
                    )
                    db.session.commit()
                    send_reference_request_mails(reference_request, reference)
                    flash(msg, "success")

            return redirect(url_for("event_actions", event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)
    return render_template(
        "event/create.html",
        admin_unit=admin_unit,
        form=form,
        event_suggestion=event_suggestion,
    )


@app.route("/event/<int:event_id>/update", methods=("GET", "POST"))
@auth_required()
def event_update(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, "event:update")

    form = UpdateEventForm(obj=event)
    prepare_event_form(form)

    if not form.is_submitted():
        form.category_ids.data = [c.id for c in event.categories]

    if form.validate_on_submit():
        update_event_with_form(event, form)

        try:
            update_event(event)
            changes = get_significant_event_changes(event)
            db.session.commit()

            if changes:
                send_referenced_event_changed_mails(event)
            flash_message(
                gettext("Event successfully updated"),
                url_for("event", event_id=event.id),
            )
            return redirect(url_for("manage_admin_unit_events", id=event.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("event/update.html", form=form, event=event)


@app.route("/event/<int:event_id>/delete", methods=("GET", "POST"))
@auth_required()
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, "event:delete")

    form = DeleteEventForm()

    if form.validate_on_submit():
        try:
            admin_unit_id = event.admin_unit.id
            db.session.delete(event)
            db.session.commit()
            flash(gettext("Event successfully deleted"), "success")
            return redirect(url_for("manage_admin_unit_events", id=admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("event/delete.html", form=form, event=event)


@app.route("/events/rrule", methods=["POST"])
def event_rrule():
    year = request.json["year"]
    month = request.json["month"]
    day = request.json["day"]
    rrule_str = request.json["rrule"]
    start = int(request.json["start"])
    batch_size = 10
    start_date = datetime(year, month, day)

    from project.dateutils import calculate_occurrences

    try:
        result = calculate_occurrences(
            start_date, '"%d.%m.%Y"', rrule_str, start, batch_size
        )
        return jsonify(result)
    except Exception as e:
        app.logger.exception(request.json)
        return getattr(e, "message", "Unknown error"), 400


def get_event_category_choices():
    return sorted(
        [(c.id, get_event_category_name(c)) for c in EventCategory.query.all()],
        key=lambda category: category[1],
    )


def prepare_event_place(form):
    if form.event_place_id.data and form.event_place_id.data > 0:
        place = db.session.get(EventPlace, form.event_place_id.data)

        if place:
            form.event_place_id.choices = [(place.id, place.name)]

    if not form.event_place_id.choices:
        form.event_place_id.choices = []


def prepare_organizer(form):
    if form.organizer_id.data and form.organizer_id.data > 0:
        organizer = db.session.get(EventOrganizer, form.organizer_id.data)

        if organizer:
            form.organizer_id.choices = [(organizer.id, organizer.name)]

    if form.co_organizer_ids.data and len(form.co_organizer_ids.data) > 0:
        co_organizers = EventOrganizer.query.filter(
            EventOrganizer.id.in_(form.co_organizer_ids.data)
        ).all()
        form.co_organizer_ids.choices = [(o.id, o.name) for o in co_organizers]

    if not form.organizer_id.choices:
        form.organizer_id.choices = []

    if not form.co_organizer_ids.choices:
        form.co_organizer_ids.choices = []


def prepare_event_form(form):
    form.category_ids.choices = get_event_category_choices()
    form.co_organizer_ids.choices = list()

    prepare_organizer(form)
    prepare_event_place(form)

    prepare_date_definition(form)


def prepare_date_definition(form):
    next_full_hour = get_next_full_hour()
    form.date_definition_template.start.data = next_full_hour

    if not form.date_definitions[0].start.data:
        form.date_definitions[0].start.data = next_full_hour


def prepare_event_form_for_suggestion(form, event_suggestion):
    form.name.data = event_suggestion.name
    form.date_definitions[0].start.data = event_suggestion.start
    form.date_definitions[0].end.data = event_suggestion.end
    form.date_definitions[0].recurrence_rule.data = event_suggestion.recurrence_rule
    form.date_definitions[0].allday.data = event_suggestion.allday
    form.external_link.data = event_suggestion.external_link
    form.description.data = event_suggestion.description

    form.ticket_link.data = event_suggestion.ticket_link
    form.tags.data = event_suggestion.tags
    form.kid_friendly.data = event_suggestion.kid_friendly
    form.accessible_for_free.data = event_suggestion.accessible_for_free
    form.age_from.data = event_suggestion.age_from
    form.age_to.data = event_suggestion.age_to
    form.target_group_origin.data = event_suggestion.target_group_origin
    form.attendance_mode.data = event_suggestion.attendance_mode
    form.registration_required.data = event_suggestion.registration_required
    form.booked_up.data = event_suggestion.booked_up
    form.expected_participants.data = event_suggestion.expected_participants
    form.price_info.data = event_suggestion.price_info

    if event_suggestion.categories:
        form.category_ids.data = [c.id for c in event_suggestion.categories]

    if event_suggestion.photo:
        form.photo.form.process(obj=event_suggestion.photo)

    if event_suggestion.event_place:
        form.event_place_id.data = event_suggestion.event_place.id
    else:
        form.event_place_choice.data = 2
        form.new_event_place.form.name.data = event_suggestion.event_place_text

    if event_suggestion.organizer:
        form.organizer_id.data = event_suggestion.organizer.id
    else:
        form.organizer_choice.data = 2
        form.new_organizer.form.name.data = event_suggestion.organizer_text

    prepare_organizer(form)
    prepare_event_place(form)


def update_event_with_form(event, form, event_suggestion=None):
    with db.session.no_autoflush:
        form.populate_obj(event)
        event.categories = EventCategory.query.filter(
            EventCategory.id.in_(form.category_ids.data)
        ).all()


def get_user_rights(event):
    return {
        "can_duplicate_event": has_access(event.admin_unit, "event:create"),
        "can_verify_event": has_access(event.admin_unit, "event:verify"),
        "can_reference_event": can_reference_event(event),
        "can_create_reference_request": can_request_event_reference(event),
        "can_create_event": has_access(event.admin_unit, "event:create"),
        "can_view_actions": current_user.is_authenticated,
        "can_update_event": has_access(event.admin_unit, "event:update"),
    }


def send_referenced_event_changed_mails(event):
    # Alle Referenzen
    references = EventReference.query.filter(EventReference.event_id == event.id).all()
    for reference in references:
        # Alle Mitglieder der AdminUnit, die das Recht haben, Requests zu verifizieren
        send_template_mails_to_admin_unit_members_async(
            reference.admin_unit_id,
            "reference_request:verify",
            "referenced_event_changed_notice",
            event=event,
            reference=reference,
        )


def send_event_report_mails(event: Event, report: dict):
    from project.services.user import find_all_users_with_role

    # Alle Mitglieder der AdminUnit, die das Recht haben, Events zu bearbeiten
    members = get_admin_unit_members_with_permission(
        event.admin_unit_id, "event:update"
    )
    users = [member.user for member in members]

    # Alle globalen Admins
    admins = find_all_users_with_role("admin")
    users.extend(
        admin for admin in admins if all(user.id != admin.id for user in users)
    )

    send_template_mails_to_users_async(
        users,
        "event_report_notice",
        event=event,
        report=report,
    )


@app.route("/event/<int:id>/ical")
def event_ical(id):
    event = get_event_with_details_or_404(id)
    can_read_event_or_401(event)

    ical_events = create_ical_events_for_event(event)

    cal = create_icalendar()
    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=event_{id}.ics"},
    )
