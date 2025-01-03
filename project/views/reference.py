from flask import abort, flash, redirect, render_template, url_for
from flask_babel import gettext
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import can_reference_event, get_admin_units_for_event_reference
from project.forms.reference import CreateEventReferenceForm
from project.models import Event, EventReference
from project.views.utils import flash_errors, handleSqlError


@app.route("/event/<int:event_id>/reference", methods=("GET", "POST"))
def event_reference_create(event_id):
    event = Event.query.get_or_404(event_id)
    user_can_reference_event = can_reference_event(event)

    if not user_can_reference_event:
        abort(401)

    form = CreateEventReferenceForm()
    form.admin_unit_id.choices = sorted(
        [
            (admin_unit.id, admin_unit.name)
            for admin_unit in get_admin_units_for_event_reference(event)
        ],
        key=lambda admin_unit: admin_unit[1],
    )

    if form.validate_on_submit():
        reference = EventReference()
        form.populate_obj(reference)
        reference.event = event

        try:
            db.session.add(reference)
            db.session.commit()
            flash(gettext("Event successfully referenced"), "success")
            return redirect(url_for("event", event_id=event.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("event/reference.html", form=form, event=event)
