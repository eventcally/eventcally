from project import app, db
from project.models import (
    Event,
    EventDate,
    EventReviewStatus,
    AdminUnit,
    EventOrganizer,
    EventCategory,
    EventSuggestion,
)
from flask import render_template, flash, url_for, redirect, request, jsonify
from flask_babelex import gettext
from project.access import (
    has_access,
    access_or_401,
    can_reference_event,
)
from project.dateutils import today
from datetime import datetime
from project.forms.event import CreateEventForm, UpdateEventForm, DeleteEventForm
from project.views.utils import (
    flash_errors,
    handleSqlError,
    flash_message,
)
from project.utils import get_event_category_name
from project.services.event import (
    upsert_event_category,
    insert_event,
    update_event,
)
from project.services.place import get_event_places
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from project.views.event_suggestion import send_event_suggestion_review_status_mail


@app.route("/event/<int:event_id>")
def event(event_id):
    event = Event.query.get_or_404(event_id)
    user_rights = get_user_rights(event)
    dates = (
        EventDate.query.with_parent(event)
        .filter(EventDate.start >= today)
        .order_by(EventDate.start)
        .all()
    )

    return render_template(
        "event/read.html", event=event, dates=dates, user_rights=user_rights
    )


@app.route("/admin_unit/<int:id>/events/create", methods=("GET", "POST"))
def event_create_for_admin_unit_id(id):
    admin_unit = AdminUnit.query.get_or_404(id)
    access_or_401(admin_unit, "event:create")

    form = CreateEventForm(
        admin_unit_id=admin_unit.id, category_ids=[upsert_event_category("Other").id]
    )
    prepare_event_form(form, admin_unit)

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

            flash_message(
                gettext("Event successfully created"),
                url_for("event", event_id=event.id),
            )
            return redirect(url_for("manage_admin_unit_events", id=event.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)
    return render_template(
        "event/create.html", form=form, event_suggestion=event_suggestion
    )


@app.route("/event/<int:event_id>/update", methods=("GET", "POST"))
def event_update(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, "event:update")

    form = UpdateEventForm(obj=event, start=event.start, end=event.end)
    prepare_event_form(form, event.admin_unit)

    if not form.is_submitted():
        form.category_ids.data = [c.id for c in event.categories]

    if form.validate_on_submit():
        update_event_with_form(event, form)

        try:
            update_event(event)
            db.session.commit()
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
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, "event:delete")

    form = DeleteEventForm()

    if form.validate_on_submit():
        if form.name.data != event.name:
            flash(gettext("Entered name does not match event name"), "danger")
        else:
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

    result = calculate_occurrences(
        start_date, '"%d.%m.%Y"', rrule_str, start, batch_size
    )
    return jsonify(result)


def get_event_category_choices():
    return sorted(
        [(c.id, get_event_category_name(c)) for c in EventCategory.query.all()],
        key=lambda category: category[1],
    )


def prepare_event_form(form, admin_unit):
    form.organizer_id.choices = [
        (o.id, o.name)
        for o in EventOrganizer.query.filter(
            EventOrganizer.admin_unit_id == admin_unit.id
        ).order_by(func.lower(EventOrganizer.name))
    ]
    form.category_ids.choices = get_event_category_choices()

    places = get_event_places(admin_unit.id)
    form.event_place_id.choices = [(p.id, p.name) for p in places]

    form.organizer_id.choices.insert(0, (0, ""))
    form.event_place_id.choices.insert(0, (0, ""))


def prepare_event_form_for_suggestion(form, event_suggestion):
    form.name.data = event_suggestion.name
    form.start.data = event_suggestion.start
    form.end.data = event_suggestion.end
    form.recurrence_rule.data = event_suggestion.recurrence_rule
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


def update_event_with_form(event, form, event_suggestion=None):
    form.populate_obj(event)
    event.categories = EventCategory.query.filter(
        EventCategory.id.in_(form.category_ids.data)
    ).all()


def get_user_rights(event):
    return {
        "can_duplicate_event": has_access(event.admin_unit, "event:create"),
        "can_verify_event": has_access(event.admin_unit, "event:verify"),
        "can_update_event": has_access(event.admin_unit, "event:update"),
        "can_reference_event": can_reference_event(event),
        "can_create_reference_request": has_access(
            event.admin_unit, "reference_request:create"
        ),
    }
