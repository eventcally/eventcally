from app import app, db
from models import User, Event, EventDate, EventReviewStatus, AdminUnit, AdminUnitMember, EventOrganizer, EventCategory
from flask import render_template, flash, url_for, redirect, request, jsonify
from flask_babelex import gettext
from flask_security import auth_required
from access import has_access, access_or_401, can_reference_event, has_admin_unit_member_permission
from dateutils import today
from datetime import datetime
from forms.event import CreateEventForm, UpdateEventForm, DeleteEventForm
from .utils import flash_errors, upsert_image_with_data, send_mail, handleSqlError
from utils import get_event_category_name
from services.event import upsert_event_category, update_event_dates_with_recurrence_rule
from services.organizer import get_event_places
from sqlalchemy.sql import asc, func
from sqlalchemy.exc import SQLAlchemyError

@app.route('/event/<int:event_id>')
def event(event_id):
    event = Event.query.get_or_404(event_id)
    user_can_verify_event = has_access(event.admin_unit, 'event:verify')
    user_can_update_event = has_access(event.admin_unit, 'event:update')

    if not event.verified and not user_can_verify_event and not user_can_update_event:
        abort(401)

    dates = EventDate.query.with_parent(event).filter(EventDate.start >= today).order_by(EventDate.start).all()

    return render_template('event/read.html',
        event=event,
        dates=dates,
        user_can_verify_event=user_can_verify_event,
        can_update_event=user_can_update_event,
        user_can_reference_event=can_reference_event(event),
        user_can_create_reference_request=has_access(event.admin_unit, 'reference_request:create'))

@app.route("/<string:au_short_name>/events/create", methods=('GET', 'POST'))
def event_create_for_admin_unit(au_short_name):
    admin_unit = AdminUnit.query.filter(AdminUnit.short_name == au_short_name).first_or_404()
    return event_create_base(admin_unit)

@app.route("/admin_unit/<int:id>/events/create", methods=('GET', 'POST'))
def event_create_for_admin_unit_id(id):
    admin_unit = AdminUnit.query.get_or_404(id)
    organizer_id = request.args.get('organizer_id') if 'organizer_id' in request.args else 0
    return event_create_base(admin_unit, organizer_id)

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
            flash(gettext('Event successfully updated'), 'success')
            return redirect(url_for('event', event_id=event.id))
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
                db.session.delete(event)
                db.session.commit()
                flash(gettext('Event successfully deleted'), 'success')
                return redirect(url_for('manage_admin_unit_events', id=admin_unit, organizer_id=event.organizer_id))
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

def event_create_base(admin_unit, organizer_id=0):
    form = CreateEventForm(admin_unit_id=admin_unit.id, organizer_id=organizer_id, category_id=upsert_event_category('Other').id)
    prepare_event_form(form, admin_unit)

    current_user_can_create_event = has_access(admin_unit, 'event:create')
    current_user_can_verify_event = has_access(admin_unit, 'event:verify')

    if not current_user_can_create_event:
        form.contact.min_entries = 1
        if len(form.contact.entries) == 0:
            form.contact.append_entry()

    if not current_user_can_verify_event:
        form.rating.choices = [(0, '0')]
        form.rating.data = 0

    if form.validate_on_submit():
        event = Event()
        update_event_with_form(event, form)
        event.admin_unit_id = admin_unit.id

        if form.event_place_choice.data == 2:
            event.event_place.organizer_id = event.organizer_id
            event.event_place.admin_unit_id = event.admin_unit_id

        if current_user_can_verify_event:
            event.review_status = EventReviewStatus.verified
        else:
            event.review_status = EventReviewStatus.inbox

        try:
            db.session.add(event)
            db.session.commit()

            if current_user_can_verify_event:
                flash(gettext('Event successfully created'), 'success')
                return redirect(url_for('event', event_id=event.id))
            else:
                send_event_inbox_mails(admin_unit, event)
                flash(gettext('Thank you so much! The event is being verified.'), 'success')
                return redirect(url_for('event_review_status', event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)
    return render_template('event/create.html', form=form)

def get_event_category_choices():
    return sorted([(c.id, get_event_category_name(c)) for c in EventCategory.query.all()], key=lambda category: category[1])

def prepare_event_form(form, admin_unit):
    form.organizer_id.choices = [(o.id, o.name) for o in EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit.id).order_by(func.lower(EventOrganizer.name))]
    form.category_id.choices = get_event_category_choices()

    if form.organizer_id.data:
        places = get_event_places(form.organizer_id.data)
        form.event_place_id.choices = [(p.id, p.name) for p in places]
    else:
        form.event_place_id.choices = list()

    form.organizer_id.choices.insert(0, (0, ''))
    form.event_place_id.choices.insert(0, (0, ''))

def update_event_with_form(event, form):
    form.populate_obj(event)

    update_event_dates_with_recurrence_rule(event, form.start.data, form.end.data)

def send_event_inbox_mails(admin_unit, event):
    members = AdminUnitMember.query.join(User).filter(AdminUnitMember.admin_unit_id == admin_unit.id).all()

    for member in members:
        if has_admin_unit_member_permission(member, 'event:verify'):
            send_mail(member.user.email,
                gettext('New event review'),
                'review_notice',
                event=event)
