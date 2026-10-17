from dependency_injector.wiring import Provide, inject
from flask import abort, flash, redirect, render_template, url_for
from flask_babel import gettext

from project.access import can_reference_event, get_admin_units_for_event_reference
from project.application.message_bus import MessageBus
from project.application.queries import GetEventDetailQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors import BaseError
from project.forms.reference import CreateEventReferenceForm
from project.views.main_blueprint import main_bp
from project.views.utils import flash_errors, handleBaseError, result_or_404


@main_bp.route("/event/<int:event_id>/reference", methods=("GET", "POST"))
@inject
def event_reference_create(
    event_id,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=event_id)))
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
        try:
            message_bus.handle_command(form.create_create_command(event.id))
            flash(gettext("Event successfully referenced"), "success")
            return redirect(url_for("main.event", event_id=event.id))
        except BaseError as e:
            flash(handleBaseError(e), "danger")
    else:
        flash_errors(form)

    return render_template("event/reference.html", form=form, event=event)
