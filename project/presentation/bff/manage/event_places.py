from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateEventPlaceCommand,
    UpdateEventPlaceCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetEventPlaceForEditQuery,
    IsEventPlaceNameTakenQuery,
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
    EventPlaceForm,
    EventPlaceLocation,
    EventPlaceNameAvailability,
    EventPlaceNameAvailabilityParams,
    EventPlaceSave,
    EventPlaceSaved,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _write_access_or_forbidden(id: int):
    if not has_access(SimpleNamespace(id=id), "event_places:write"):
        raise UnauthorizedError()


def _place_or_404(id: int, place_id: int, query_bus: QueryBus):
    _write_access_or_forbidden(id)
    place = result_or_404(query_bus.handle(GetEventPlaceForEditQuery(id=place_id)))

    # Do not reveal the places of other organizations.
    if place.admin_unit_id != id:
        abort(404)

    return place


def _name_errors(query_bus: QueryBus, id: int, name: str, exclude_id=None) -> list:
    if query_bus.handle(
        IsEventPlaceNameTakenQuery(admin_unit_id=id, name=name, exclude_id=exclude_id)
    ):
        return [(["name"], gettext("A place already exists with this name."))]

    return []


def _saved(id: int, place_id: int, text: str) -> EventPlaceSaved:
    flash(text, "success")
    return EventPlaceSaved(
        id=place_id, redirect_url=url_for("manage_admin_unit.event_places", id=id)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-places/create-form",
    response=EventPlaceForm,
    summary="Get the form to create a place",
)
@inject
def get_event_place_create_form(
    id: int, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    _write_access_or_forbidden(id)
    return EventPlaceForm(
        location=EventPlaceLocation(), licenses=license_choices(query_bus)
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-places/<int:place_id>",
    response=EventPlaceForm,
    summary="Get the form to update a place",
)
@inject
def get_event_place_form(
    id: int,
    place_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    place = _place_or_404(id, place_id, query_bus)

    return EventPlaceForm(
        id=place.id,
        name=place.name,
        url=place.url,
        description=place.description,
        location=location_form_value(place.location),
        photo=image_form_value(place.photo),
        licenses=license_choices(query_bus),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-places/name-availability",
    query=EventPlaceNameAvailabilityParams,
    response=EventPlaceNameAvailability,
    summary="Whether the name of a place is taken",
)
@inject
def get_event_place_name_availability(
    id: int,
    query: EventPlaceNameAvailabilityParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    result = EventPlaceNameAvailability()

    if query.name:
        result.name_taken = query_bus.handle(
            IsEventPlaceNameTakenQuery(
                admin_unit_id=id, name=query.name, exclude_id=query.exclude_id
            )
        )

    return result


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-places",
    method="POST",
    body=EventPlaceSave,
    response=EventPlaceSaved,
    status=201,
    summary="Create a place",
)
@inject
def create_event_place(
    id: int,
    body: EventPlaceSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _write_access_or_forbidden(id)
    errors = _name_errors(query_bus, id, body.name)
    photo = image_from_save(body.photo, None, errors, ["photo"])

    if errors:
        raise FieldValidationError(errors=errors)

    result = message_bus.handle_command(
        CreateEventPlaceCommand(
            actor=actor(),
            admin_unit_id=id,
            name=body.name,
            url=body.url,
            description=body.description,
            location=location_value_object(body.location),
            photo=photo,
        )
    )

    return _saved(
        id,
        result.id,
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=gettext("Place"),
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/event-places/<int:place_id>",
    method="PUT",
    body=EventPlaceSave,
    response=EventPlaceSaved,
    summary="Update a place",
)
@inject
def update_event_place(
    id: int,
    place_id: int,
    body: EventPlaceSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    place = _place_or_404(id, place_id, query_bus)
    errors = _name_errors(query_bus, id, body.name, exclude_id=place_id)
    photo = image_from_save(body.photo, place.photo, errors, ["photo"])

    if errors:
        raise FieldValidationError(errors=errors)

    message_bus.handle_command(
        UpdateEventPlaceCommand(
            actor=actor(),
            id=place_id,
            name=body.name,
            url=body.url,
            description=body.description,
            location=location_value_object(body.location),
            photo=photo,
        )
    )

    return _saved(
        id,
        place_id,
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=gettext("Place"),
        ),
    )
