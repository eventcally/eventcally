from flask import Response, flash, redirect, render_template, url_for
from flask_babelex import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import access_or_401, get_admin_unit_for_manage_or_404
from project.dateutils import create_icalendar
from project.forms.organizer import (
    CreateOrganizerForm,
    DeleteOrganizerForm,
    UpdateOrganizerForm,
)
from project.models import EventOrganizer
from project.services.organizer import create_ical_events_for_organizer
from project.views.utils import flash_errors, handleSqlError, non_match_for_deletion


@app.route("/manage/admin_unit/<int:id>/organizers/create", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_organizer_create(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    access_or_401(admin_unit, "organizer:create")

    form = CreateOrganizerForm()

    if form.validate_on_submit():
        organizer = EventOrganizer()
        organizer.admin_unit_id = admin_unit.id
        update_organizer_with_form(organizer, form)

        try:
            db.session.add(organizer)
            db.session.commit()
            flash(gettext("Organizer successfully created"), "success")
            return redirect(
                url_for("manage_admin_unit_organizers", id=organizer.admin_unit_id)
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)
    return render_template("organizer/create.html", form=form)


@app.route("/organizer/<int:id>/update", methods=("GET", "POST"))
@auth_required()
def organizer_update(id):
    organizer = EventOrganizer.query.get_or_404(id)
    access_or_401(organizer.adminunit, "organizer:update")

    form = UpdateOrganizerForm(obj=organizer)

    if form.validate_on_submit():
        update_organizer_with_form(organizer, form)

        try:
            db.session.commit()
            flash(gettext("Organizer successfully updated"), "success")
            return redirect(
                url_for("manage_admin_unit_organizers", id=organizer.admin_unit_id)
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("organizer/update.html", form=form, organizer=organizer)


@app.route("/organizer/<int:id>/delete", methods=("GET", "POST"))
@auth_required()
def organizer_delete(id):
    organizer = EventOrganizer.query.get_or_404(id)
    access_or_401(organizer.adminunit, "organizer:delete")

    form = DeleteOrganizerForm()

    if form.validate_on_submit():
        if non_match_for_deletion(form.name.data, organizer.name):
            flash(gettext("Entered name does not match organizer name"), "danger")
        else:
            try:
                db.session.delete(organizer)
                db.session.commit()
                flash(gettext("Organizer successfully deleted"), "success")
                return redirect(
                    url_for("manage_admin_unit_organizers", id=organizer.admin_unit_id)
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("organizer/delete.html", form=form, organizer=organizer)


def update_organizer_with_form(organizer, form):
    form.populate_obj(organizer)


@app.route("/organizers")
@app.route("/organizers/<path:path>")
def organizers(path=None):
    return render_template("organizer/main.html")


@app.route("/organizers/<int:id>/ical")
def organizer_ical(id):
    organizer = EventOrganizer.query.get_or_404(id)

    cal = create_icalendar()
    cal.add("x-wr-calname", organizer.name)
    ical_events = create_ical_events_for_organizer(organizer)

    for ical_event in ical_events:
        cal.add_component(ical_event)

    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=organizer_{id}.ics"},
    )
