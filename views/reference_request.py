from app import app, db
from .utils import get_pagination_urls, flash_errors, handleSqlError
from forms.reference_request import CreateEventReferenceRequestForm, DeleteReferenceRequestForm
from flask import render_template, flash, redirect, url_for
from flask_babelex import gettext
from flask_security import auth_required
from models import EventReferenceRequest, Event, AdminUnit
from access import access_or_401, get_admin_unit_for_manage_or_404

@app.route('/event/<int:event_id>/reference_request', methods=('GET', 'POST'))
def event_reference_request(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, 'reference_request:create')

    form = CreateEventReferenceRequestForm()
    form.admin_unit_id.choices = sorted([(admin_unit.id, admin_unit.name) for admin_unit in AdminUnit.query.all()], key=lambda admin_unit: admin_unit[1])

    if form.validate_on_submit():
        request = EventReferenceRequest()
        form.populate_obj(request)
        request.event = event

        try:
            db.session.add(request)
            db.session.commit()
            flash(gettext('Request successfully created'), 'success')
            return redirect(url_for('event', event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event/reference_request.html',
        form=form,
        event=event)

@app.route('/manage/admin_unit/<int:id>/reference_requests')
@auth_required()
def manage_admin_unit_reference_requests(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    requests = EventReferenceRequest.query.filter(EventReferenceRequest.admin_unit_id == admin_unit.id).order_by(EventReferenceRequest.created_at).paginate()

    return render_template('manage/reference_requests.html',
        admin_unit=admin_unit,
        requests=requests.items,
        pagination=get_pagination_urls(requests, id=id))

# @app.route('/reference_request/<int:id>/review', methods=('GET', 'POST'))
# def event_reference_request_review(id):
#     request = EventReferenceRequest.query.get_or_404(id)
#     event = Event.query.get_or_404(request.event_id)
#     dates = EventDate.query.with_parent(event).filter(EventDate.start >= today).order_by(EventDate.start).all()
#     user_can_verify_event = can_verify_event(event)

#     if not user_can_verify_event:
#         abort(401)

#     form = ReviewEventForm(obj=event)

#     if form.validate_on_submit():
#         form.populate_obj(event)

#         if event.review_status != EventReviewStatus.rejected:
#             event.rejection_resaon = None

#         if event.rejection_resaon == 0:
#             event.rejection_resaon = None

#         try:
#             db.session.commit()
#             send_event_review_status_mail(event)
#             flash(gettext('Event successfully updated'), 'success')
#             return redirect(url_for('manage_admin_unit_event_reviews', id=event.admin_unit_id))
#         except SQLAlchemyError as e:
#             db.session.rollback()
#             flash(handleSqlError(e), 'danger')
#     else:
#         flash_errors(form)

#     return render_template('event/review.html',
#         form=form,
#         dates=dates,
#         event=event)

# @app.route('/reference/<int:id>/delete', methods=('GET', 'POST'))
# def reference_delete(id):
#     reference = EventReference.query.get_or_404(id)

#     if not can_delete_reference(reference):
#         abort(401)

#     form = DeleteReferenceForm()

#     if form.validate_on_submit():
#         if form.name.data != reference.event.name:
#             flash(gettext('Entered name does not match event name'), 'danger')
#         else:
#             try:
#                 db.session.delete(reference)
#                 db.session.commit()
#                 flash(gettext('Reference successfully deleted'), 'success')
#                 return redirect(url_for('manage_admin_unit_references', id=reference.admin_unit_id))
#             except SQLAlchemyError as e:
#                 db.session.rollback()
#                 flash(handleSqlError(e), 'danger')
#     else:
#         flash_errors(form)

#     return render_template('reference/delete.html',
#         form=form,
#         reference=reference)