from dependency_injector.wiring import Provide, inject
from flask import url_for

from project.application.queries import GetEventOrganizerQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.schemas import (
    PublicOrganizationRef,
    PublicOrganizer,
    PublicOrganizerLocation,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.urls import url_for_image


@bff_route(
    bff_public_bp,
    "/organizers/<int:id>",
    response=PublicOrganizer,
    summary="Get organizer",
)
@inject
def get_organizer(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    organizer = result_or_404(query_bus.handle(GetEventOrganizerQuery(id=id)))

    location = None
    if organizer.location and (
        organizer.location.street
        or organizer.location.postalCode
        or organizer.location.city
    ):
        location = PublicOrganizerLocation(
            street=organizer.location.street,
            postal_code=organizer.location.postalCode,
            city=organizer.location.city,
        )

    return PublicOrganizer(
        id=organizer.id,
        name=organizer.name,
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
        location=location,
        logo_url=url_for_image(organizer.logo, s=120) if organizer.logo else None,
        organization=PublicOrganizationRef(
            id=organizer.admin_unit.id, name=organizer.admin_unit.name
        ),
        ical_url=url_for("main.organizer_ical", id=organizer.id, _external=True),
    )
