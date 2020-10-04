from app import app, db
from models import EventOrganizer, EventPlace, Location
from flask import render_template, flash, url_for, redirect, request, jsonify
from flask_babelex import gettext
from flask_security import auth_required
from access import has_access, access_or_401, get_admin_unit_for_manage_or_404
from forms.event_place import UpdateEventPlaceForm, CreateEventPlaceForm
from .utils import flash_errors, upsert_image_with_data, send_mail, handleSqlError
from sqlalchemy.sql import asc, func
from sqlalchemy.exc import SQLAlchemyError

@app.route('/manage/organizer/<int:id>/places/create', methods=('GET', 'POST'))
@auth_required()
def manage_organizer_places_create(id):
    organizer = EventOrganizer.query.get_or_404(id)
    access_or_401(organizer.adminunit, 'place:create')

    form = CreateEventPlaceForm()

    if form.validate_on_submit():
        place = EventPlace()
        place.organizer_id = organizer.id
        place.admin_unit_id = organizer.admin_unit_id
        place.location = Location()
        update_event_place_with_form(place, form)

        try:
            db.session.add(place)
            db.session.commit()
            flash(gettext('Place successfully created'), 'success')
            return redirect(url_for('manage_organizer_event_places', organizer_id=organizer.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    return render_template('event_place/create.html', form=form)

@app.route('/event_place/<int:id>/update', methods=('GET', 'POST'))
@auth_required()
def event_place_update(id):
    place = EventPlace.query.get_or_404(id)
    access_or_401(place.adminunit, 'place:update')

    form = UpdateEventPlaceForm(obj=place)

    if form.validate_on_submit():
        update_event_place_with_form(place, form)

        try:
            db.session.commit()
            flash(gettext('Place successfully updated'), 'success')
            return redirect(url_for('manage_organizer_event_places', organizer_id=place.organizer.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')

    return render_template('event_place/update.html',
        form=form,
        place=place)

def update_event_place_with_form(place, form):
    form.populate_obj(place)

    if form.photo_file.data:
        fs = form.photo_file.data
        place.photo = upsert_image_with_data(place.photo, fs.read(), fs.content_type)

