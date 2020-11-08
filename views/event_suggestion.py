from app import app, db
from models import EventSuggestion, User, Event, EventDate, EventReviewStatus, AdminUnit, AdminUnitMember, EventOrganizer, EventCategory
from flask import render_template, flash, url_for, redirect, request, jsonify, abort
from flask_babelex import gettext
from flask_security import current_user
from access import has_access, access_or_401, can_reference_event, has_admin_unit_member_permission
from dateutils import today
from datetime import datetime
from forms.event_suggestion import RejectEventSuggestionForm
from .utils import flash_errors, send_mail, handleSqlError, flash_message
from utils import get_event_category_name
from services.event import upsert_event_category, update_event_dates_with_recurrence_rule
from sqlalchemy.sql import asc, func
from sqlalchemy.exc import SQLAlchemyError

@app.route('/event_suggestion/<int:event_suggestion_id>/review')
def event_suggestion_review(event_suggestion_id):
    event_suggestion = EventSuggestion.query.get_or_404(event_suggestion_id)
    access_or_401(event_suggestion.admin_unit, 'event:verify')

    return render_template('event_suggestion/review.html',
        admin_unit=event_suggestion.admin_unit,
        event_suggestion=event_suggestion)

@app.route('/event_suggestion/<int:event_suggestion_id>/reject', methods=('GET', 'POST'))
def event_suggestion_reject(event_suggestion_id):
    event_suggestion = EventSuggestion.query.get_or_404(event_suggestion_id)
    access_or_401(event_suggestion.admin_unit, 'event:verify')

    if event_suggestion.verified:
        return redirect(url_for('event_suggestion_review', event_suggestion_id=event_suggestion.id))

    form = RejectEventSuggestionForm(obj=event_suggestion)

    if form.validate_on_submit():
        form.populate_obj(event_suggestion)
        event_suggestion.review_status = EventReviewStatus.rejected

        if event_suggestion.rejection_resaon == 0:
            event_suggestion.rejection_resaon = None

        try:
            db.session.commit()
            send_event_suggestion_review_status_mail(event_suggestion)
            flash(gettext('Event suggestion successfully rejected'), 'success')
            return redirect(url_for('manage_admin_unit_event_reviews', id=event_suggestion.admin_unit_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), 'danger')
    else:
        flash_errors(form)

    return render_template('event_suggestion/reject.html',
        form=form,
        admin_unit=event_suggestion.admin_unit,
        event_suggestion=event_suggestion)

@app.route('/event_suggestion/<int:event_suggestion_id>/review_status')
def event_suggestion_review_status(event_suggestion_id):
    event_suggestion = EventSuggestion.query.get_or_404(event_suggestion_id)

    return render_template('event_suggestion/review_status.html',
        event_suggestion=event_suggestion)

def send_event_suggestion_review_status_mail(event_suggestion):
    if event_suggestion.contact_email and event_suggestion.contact_email_notice:
        send_mail(event_suggestion.contact_email,
            gettext('Event review status updated'),
            'review_status_notice',
            event_suggestion=event_suggestion)
