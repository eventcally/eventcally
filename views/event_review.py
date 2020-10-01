from app import app, db
from models import Event, EventDate, EventReviewStatus, AdminUnitMember
from flask import render_template, flash, url_for, redirect
from flask_babelex import gettext
from flask_security import auth_required
from access import has_access, access_or_401, can_reference_event
from dateutils import today
from forms.event import ReviewEventForm
from .utils import flash_errors, send_mail
from sqlalchemy.exc import SQLAlchemyError

@app.route('/event/<int:event_id>/review', methods=('GET', 'POST'))
def event_review(event_id):
    event = Event.query.get_or_404(event_id)
    access_or_401(event.admin_unit, 'event:verify')

    form = ReviewEventForm(obj=event)

    if form.validate_on_submit():
        form.populate_obj(event)

        if event.review_status != EventReviewStatus.rejected:
            event.rejection_resaon = None

        if event.rejection_resaon == 0:
            event.rejection_resaon = None

        try:
            db.session.commit()
            send_event_review_status_mail(event)
            flash(gettext('Event successfully updated'), 'success')
            return redirect(url_for('manage_admin_unit_event_reviews', id=event.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    dates = EventDate.query.with_parent(event).filter(EventDate.start >= today).order_by(EventDate.start).all()
    return render_template('event/review.html',
        form=form,
        dates=dates,
        event=event)

@app.route('/event/<int:event_id>/review_status')
def event_review_status(event_id):
    event = Event.query.get_or_404(event_id)

    return render_template('event/review_status.html',
        event=event)

def send_event_review_status_mail(event):
    if event.contact and event.contact.email:
        send_mail(event.contact.email,
            gettext('Event review status updated'),
            'review_status_notice',
            event=event)