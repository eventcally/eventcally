from flask import abort, flash, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required
from sqlalchemy.exc import SQLAlchemyError

from project import app, db
from project.access import (
    access_or_401,
    can_reference_event,
    get_admin_unit_for_manage_or_404,
    get_admin_units_for_event_reference,
    has_access,
)
from project.forms.reference import (
    CreateEventReferenceForm,
    DeleteReferenceForm,
    UpdateEventReferenceForm,
)
from project.models import Event, EventReference
from project.services.reference import (
    get_reference_incoming_query,
    get_reference_outgoing_query,
)
from project.services.search_params import EventReferenceSearchParams
from project.views.utils import flash_errors, get_pagination_urls, handleSqlError


@app.route("/reference/<int:id>")
@auth_required()
def event_reference(id):
    reference = EventReference.query.get_or_404(id)
    access_or_401(reference.admin_unit, "reference:read")

    user_rights = {
        "can_update_reference": has_access(reference.admin_unit, "reference:update"),
        "can_delete_reference": has_access(reference.admin_unit, "reference:delete"),
    }

    return render_template(
        "reference/read.html",
        user_rights=user_rights,
        reference=reference,
        event=reference.event,
    )


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


@app.route("/reference/<int:id>/update", methods=("GET", "POST"))
@auth_required()
def event_reference_update(id):
    reference = EventReference.query.get_or_404(id)
    access_or_401(reference.admin_unit, "reference:update")

    form = UpdateEventReferenceForm(obj=reference)

    if form.validate_on_submit():
        form.populate_obj(reference)

        try:
            db.session.commit()
            flash(gettext("Reference successfully updated"), "success")
            return redirect(
                url_for(
                    "manage_admin_unit_references_incoming", id=reference.admin_unit_id
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("reference/update.html", form=form, reference=reference)


@app.route("/manage/admin_unit/<int:id>/references/incoming")
@auth_required()
def manage_admin_unit_references_incoming(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)
    params = EventReferenceSearchParams()
    params.admin_unit_id = admin_unit.id
    references = get_reference_incoming_query(params).paginate()

    return render_template(
        "manage/references_incoming.html",
        admin_unit=admin_unit,
        references=references.items,
        pagination=get_pagination_urls(references, id=id),
    )


@app.route("/manage/admin_unit/<int:id>/references/outgoing")
@auth_required()
def manage_admin_unit_references_outgoing(id):
    admin_unit = get_admin_unit_for_manage_or_404(id)

    params = EventReferenceSearchParams()
    params.admin_unit_id = admin_unit.id
    references = get_reference_outgoing_query(params).paginate()

    return render_template(
        "manage/references_outgoing.html",
        admin_unit=admin_unit,
        references=references.items,
        pagination=get_pagination_urls(references, id=id),
    )


@app.route("/reference/<int:id>/delete", methods=("GET", "POST"))
@auth_required()
def reference_delete(id):
    reference = EventReference.query.get_or_404(id)
    access_or_401(reference.admin_unit, "reference:delete")

    form = DeleteReferenceForm()

    if form.validate_on_submit():
        try:
            db.session.delete(reference)
            db.session.commit()
            flash(gettext("Reference successfully deleted"), "success")
            return redirect(
                url_for(
                    "manage_admin_unit_references_incoming",
                    id=reference.admin_unit_id,
                )
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(handleSqlError(e), "danger")
    else:
        flash_errors(form)

    return render_template("reference/delete.html", form=form, reference=reference)
