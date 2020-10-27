from app import app, db
from models import User, Event, EventDate, EventReviewStatus, AdminUnit, AdminUnitMember, EventOrganizer, EventCategory, EventSuggestion
from flask import render_template, flash, url_for, redirect, request, jsonify, abort
from flask_babelex import gettext
from flask_security import auth_required
from access import has_access, access_or_401, can_reference_event, has_admin_unit_member_permission
from dateutils import today
from datetime import datetime
from forms.event import CreateEventForm, UpdateEventForm, DeleteEventForm
from .utils import flash_errors, upsert_image_with_data, send_mail, handleSqlError, flash_message
from utils import get_event_category_name
from services.event import upsert_event_category, update_event_dates_with_recurrence_rule
from services.place import get_event_places
from sqlalchemy.sql import asc, func
from sqlalchemy.exc import SQLAlchemyError

@app.route('/event/<int:event_id>')
def event(event_id):
    event = Event.query.get_or_404(event_id)
    user_rights = get_user_rights(event)
    dates = EventDate.query.with_parent(event).filter(EventDate.start >= today).order_by(EventDate.start).all()

    return render_template('event/read.html',
        event=event,
        dates=dates,
        user_rights=user_rights)

@app.route("/admin_unit/<int:id>/events/create", methods=('GET', 'POST'))
def event_create_for_admin_unit_id(id):
    admin_unit = AdminUnit.query.get_or_404(id)
    access_or_401(admin_unit, 'event:create')

    form = CreateEventForm(admin_unit_id=admin_unit.id, category_id=upsert_event_category('Other').id)
    prepare_event_form(form, admin_unit)

    event_suggestion_id = int(request.args.get('event_suggestion_id')) if 'event_suggestion_id' in request.args else 0
    event_suggestion = None

    if event_suggestion_id > 0:
        event_suggestion = EventSuggestion.query.get_or_404(event_suggestion_id)
        access_or_401(event_suggestion.admin_unit, 'event:verify')
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
            db.session.add(event)
            db.session.commit()

            flash_message(gettext('Event successfully created'), url_for('event', event_id=event.id))
            return redirect(url_for('manage_admin_unit_events', id=event.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)
    return render_template('event/create.html', form=form, event_suggestion=event_suggestion)

@app.route('/event/<int:event_id>/update', methods=('GET', 'POST'))
def event_update(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, 'event:update')

    form = UpdateEventForm(obj=event,start=event.start,end=event.end)
    prepare_event_form(form, event.admin_unit)

    if form.validate_on_submit():
        update_event_with_form(event, form)

        try:
            db.session.commit()
            flash_message(gettext('Event successfully updated'), url_for('event', event_id=event.id))
            return redirect(url_for('manage_admin_unit_events', id=event.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/update.html',
        form=form,
        event=event)

@app.route('/event/<int:event_id>/delete', methods=('GET', 'POST'))
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, 'event:delete')

    form = DeleteEventForm()

    if form.validate_on_submit():
        if form.name.data != event.name:
            flash(gettext('Entered name does not match event name'), 'danger')
        else:
            try:
                admin_unit_id = event.admin_unit.id
                db.session.delete(event)
                db.session.commit()
                flash(gettext('Event successfully deleted'), 'success')
                return redirect(url_for('manage_admin_unit_events', id=admin_unit_id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/delete.html',
        form=form,
        event=event)

@app.route("/events/rrule", methods=['POST'])
def event_rrule():
    year = request.json['year']
    month = request.json['month']
    day = request.json['day']
    rrule_str = request.json['rrule']
    output_format = request.json['format']
    start = int(request.json['start'])
    batch_size = 10
    start_date = datetime(year, month, day)

    from dateutils import calculate_occurrences
    result = calculate_occurrences(start_date, '"%d.%m.%Y"', rrule_str, start, batch_size)
    return jsonify(result)

def get_event_category_choices():
    return sorted([(c.id, get_event_category_name(c)) for c in EventCategory.query.all()], key=lambda category: category[1])

def prepare_event_form(form, admin_unit):
    form.organizer_id.choices = [(o.id, o.name) for o in EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name))]
    form.category_id.choices = get_event_category_choices()

    places = get_event_places(admin_unit.id)
    form.event_place_id.choices = [(p.id, p.name) for p in places]

    form.organizer_id.choices.insert(0, (0, ''))
    form.event_place_id.choices.insert(0, (0, ''))

def prepare_event_form_for_suggestion(form, event_suggestion):
    form.name.data = event_suggestion.name
    form.start.data = event_suggestion.start
    form.description.data = event_suggestion.description
    form.external_link.data = event_suggestion.external_link

    if event_suggestion.photo:
        form.photo.form.copyright_text.data = event_suggestion.photo.copyright_text
        form.photo.object_data = event_suggestion.photo

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

def update_event_with_form(event, form, event_suggestion = None):
    form.populate_obj(event)

    if event_suggestion and event_suggestion.photo and event.photo and event.photo.data is None and not form.photo.delete_flag.data:
        event.photo.data = event_suggestion.photo.data
        event.photo.encoding_format = event_suggestion.photo.encoding_format

    update_event_dates_with_recurrence_rule(event, form.start.data, form.end.data)

def get_user_rights(event):
    return {
        "can_verify_event": has_access(event.admin_unit, 'event:verify'),
        "can_update_event": has_access(event.admin_unit, 'event:update'),
        "can_reference_event": can_reference_event(event),
        "can_create_reference_request": has_access(event.admin_unit, 'reference_request:create')
    }