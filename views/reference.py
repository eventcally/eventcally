from app import app, db
from .utils import get_pagination_urls, flash_errors, handleSqlError
from access import get_admin_unit_for_manage_or_404, get_admin_units_for_event_reference
from forms.reference import CreateEventReferenceForm, UpdateEventReferenceForm, DeleteReferenceForm
from flask import render_template, flash, redirect, url_for
from flask_babelex import gettext
from flask_security import auth_required
from models import EventReference, Event
from access import access_or_401, can_reference_event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import desc

@app.route('/event/<int:event_id>/reference', methods=('GET', 'POST'))
def event_reference(event_id):
    event = Event.query.get_or_404(event_id)
    user_can_reference_event = can_reference_event(event)

    if not user_can_reference_event:
        abort(401)

    form = CreateEventReferenceForm()
    form.admin_unit_id.choices = sorted([(admin_unit.id, admin_unit.name) for admin_unit in get_admin_units_for_event_reference(event)], key=lambda admin_unit: admin_unit[1])

    if form.validate_on_submit():
        reference = EventReference()
        form.populate_obj(reference)
        reference.event = event

        try:
            db.session.add(reference)
            db.session.commit()
            flash(gettext('Event successfully referenced'), 'success')
            return redirect(url_for('event', event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/reference.html',
        form=form,
        event=event)

@app.route('/reference/<int:id>/update', methods=('GET', 'POST'))
def event_reference_update(id):
    reference = EventReference.query.get_or_404(id)
    access_or_401(reference.admin_unit, 'reference:update')

    form = UpdateEventReferenceForm(obj=reference)

    if form.validate_on_submit():
        form.populate_obj(reference)

        try:
            db.session.commit()
            flash(gettext('Reference successfully updated'), 'success')
            return redirect(url_for('manage_admin_unit_references_incoming', id=reference.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('reference/update.html',
        form=form,
        reference=reference)

@app.route('/manage/admin_unit/<int:id>/references/incoming')
@auth_required()
def manage_admin_unit_references_incoming(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    references = EventReference.query.filter(EventReference.admin_unit_id == admin_unit.id).order_by(desc(EventReference.created_at)).paginate()

    return render_template('manage/references_incoming.html',
        admin_unit=admin_unit,
        references=references.items,
        pagination=get_pagination_urls(references, id=id))

@app.route('/manage/admin_unit/<int:id>/references/outgoing')
@auth_required()
def manage_admin_unit_references_outgoing(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    references = EventReference.query.join(Event).filter(Event.admin_unit_id == admin_unit.id).order_by(desc(EventReference.created_at)).paginate()

    return render_template('manage/references_outgoing.html',
        admin_unit=admin_unit,
        references=references.items,
        pagination=get_pagination_urls(references, id=id))

@app.route('/reference/<int:id>/delete', methods=('GET', 'POST'))
def reference_delete(id):
    reference = EventReference.query.get_or_404(id)
    access_or_401(reference.admin_unit, 'reference:delete')

    form = DeleteReferenceForm()

    if form.validate_on_submit():
        if form.name.data != reference.event.name:
            flash(gettext('Entered name does not match event name'), 'danger')
        else:
            try:
                db.session.delete(reference)
                db.session.commit()
                flash(gettext('Reference successfully deleted'), 'success')
                return redirect(url_for('manage_admin_unit_references_incoming', id=reference.admin_unit_id))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('reference/delete.html',
        form=form,
        reference=reference)