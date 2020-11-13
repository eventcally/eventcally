from project import app, db
from project.models import EventPlace, Location
from flask import render_template, flash, url_for, redirect
from flask_babelex import gettext
from flask_security import auth_required
from project.access import access_or_401, get_admin_unit_for_manage_or_404
from project.forms.event_place import (
    UpdateEventPlaceForm,
    CreateEventPlaceForm,
    DeleteEventPlaceForm,
)
from project.views.utils import (
    flash_errors,
    handleSqlError,
)
from sqlalchemy.exc import SQLAlchemyError


@app.route("/manage/admin_unit/<int:id>/places/create", methods=("GET", "POST"))
@auth_required()
def manage_admin_unit_places_create(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    access_or_401(admin_unit, "place:create")

    form = CreateEventPlaceForm()

    if form.validate_on_submit():
        place = EventPlace()
        place.admin_unit_id = admin_unit.id
        place.location = Location()
        update_event_place_with_form(place, form)

        try:
            db.session.add(place)
            db.session.commit()
            flash(gettext("Place successfully created"), "success")
            return redirect(url_for("manage_admin_unit_event_places", id=admin_unit.id))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    return render_template("event_place/create.html", form=form)


@app.route("/event_place/<int:id>/update", methods=("GET", "POST"))
@auth_required()
def event_place_update(id):
    place = EventPlace.query.get_or_404(id)
    access_or_401(place.adminunit, "place:update")

    form = UpdateEventPlaceForm(obj=place)

    if form.validate_on_submit():
        update_event_place_with_form(place, form)

        try:
            db.session.commit()
            flash(gettext("Place successfully updated"), "success")
            return redirect(
                url_for("manage_admin_unit_event_places", id=place.admin_unit_id)
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")

    return render_template("event_place/update.html", form=form, place=place)


@app.route("/event_place/<int:id>/delete", methods=("GET", "POST"))
@auth_required()
def event_place_delete(id):
    place = EventPlace.query.get_or_404(id)
    access_or_401(place.adminunit, "place:delete")

    form = DeleteEventPlaceForm()

    if form.validate_on_submit():
        if form.name.data != place.name:
            flash(gettext("Entered name does not match place name"), "danger")
        else:
            try:
                admin_unit_id = place.admin_unit_id
                db.session.delete(place)
                db.session.commit()
                flash(gettext("Place successfully deleted"), "success")
                return redirect(
                    url_for("manage_admin_unit_event_places", id=admin_unit_id)
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("event_place/delete.html", form=form, place=place)


def update_event_place_with_form(place, form):
    form.populate_obj(place)
