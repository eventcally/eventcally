from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateEventOrganizerCommand,
    UpdateEventOrganizerCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetEventOrganizerForEditQuery,
    IsEventOrganizerNameTakenQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.image_form import image_form_value, image_from_save
from project.presentation.bff.manage.organization_form import (
    actor,
    license_choices,
    location_form_value,
    location_value_object,
)
from project.presentation.bff.manage.schemas import (
    EventOrganizerForm,
    EventOrganizerNameAvailability,
    EventOrganizerNameAvailabilityParams,
    EventOrganizerSave,
    EventOrganizerSaved,
    EventPlaceLocation,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _write_access_or_forbidden(id: int):
    if not has_access(SimpleNamespace(id=id), "event_organizers:write"):
        raise UnauthorizedError()


def _organizer_or_404(id: int, organizer_id: int, query_bus: QueryBus):
    _write_access_or_forbidden(id)
    organizer = result_or_404(
        query_bus.handle(GetEventOrganizerForEditQuery(id=organizer_id))
    )

    # Do not reveal the organizers of other organizations.
    if organizer.admin_unit_id != id:
        abort(404)

    return organizer


def _name_errors(query_bus: QueryBus, id: int, name: str, exclude_id=None) -> list:
    if query_bus.handle(
        IsEventOrganizerNameTakenQuery(
            admin_unit_id=id, name=name, exclude_id=exclude_id
        )
    ):
        return [(["name"], gettext("An organizer already exists with this name."))]

    return []


def _saved(id: int, organizer_id: int, text: str, inline=False) -> EventOrganizerSaved:
    if not inline:
        flash(text, "success")

    return EventOrganizerSaved(
        id=organizer_id,
        redirect_url=url_for("manage_admin_unit.event_organizers", id=id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-organizers/create-form",
    response=EventOrganizerForm,
    summary="Get the form to create an organizer",
)
@inject
def get_event_organizer_create_form(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    _write_access_or_forbidden(id)
    return EventOrganizerForm(
        location=EventPlaceLocation(), licenses=license_choices(query_bus)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-organizers/<int:organizer_id>",
    response=EventOrganizerForm,
    summary="Get the form to update an organizer",
)
@inject
def get_event_organizer_form(
    id: int,
    organizer_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organizer = _organizer_or_404(id, organizer_id, query_bus)

    return EventOrganizerForm(
        id=organizer.id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        location=location_form_value(organizer.location),
        logo=image_form_value(organizer.logo),
        licenses=license_choices(query_bus),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-organizers/name-availability",
    query=EventOrganizerNameAvailabilityParams,
    response=EventOrganizerNameAvailability,
    summary="Whether the name of an organizer is taken",
)
@inject
def get_event_organizer_name_availability(
    id: int,
    query: EventOrganizerNameAvailabilityParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    result = EventOrganizerNameAvailability()

    if query.name:
        result.name_taken = query_bus.handle(
            IsEventOrganizerNameTakenQuery(
                admin_unit_id=id, name=query.name, exclude_id=query.exclude_id
            )
        )

    return result


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-organizers",
    method="POST",
    body=EventOrganizerSave,
    response=EventOrganizerSaved,
    status=201,
    summary="Create an organizer",
)
@inject
def create_event_organizer(
    id: int,
    body: EventOrganizerSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    errors = _name_errors(query_bus, id, body.name)
    logo = image_from_save(body.logo, None, errors, ["logo"])

    if errors:
        raise FieldValidationError(errors=errors)

    result = message_bus.handle_command(
        CreateEventOrganizerCommand(
            actor=actor(),
            admin_unit_id=id,
            name=body.name,
            url=body.url,
            email=body.email,
            phone=body.phone,
            fax=body.fax,
            location=location_value_object(body.location),
            logo=logo,
        )
    )

    return _saved(
        id,
        result.id,
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=gettext("Event organizer"),
        ),
        inline=body.inline,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-organizers/<int:organizer_id>",
    method="PUT",
    body=EventOrganizerSave,
    response=EventOrganizerSaved,
    summary="Update an organizer",
)
@inject
def update_event_organizer(
    id: int,
    organizer_id: int,
    body: EventOrganizerSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organizer = _organizer_or_404(id, organizer_id, query_bus)
    errors = _name_errors(query_bus, id, body.name, exclude_id=organizer_id)
    logo = image_from_save(body.logo, organizer.logo, errors, ["logo"])

    if errors:
        raise FieldValidationError(errors=errors)

    message_bus.handle_command(
        UpdateEventOrganizerCommand(
            actor=actor(),
            id=organizer_id,
            name=body.name,
            url=body.url,
            email=body.email,
            phone=body.phone,
            fax=body.fax,
            location=location_value_object(body.location),
            logo=logo,
        )
    )

    return _saved(
        id,
        organizer_id,
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=gettext("Event organizer"),
        ),
    )
