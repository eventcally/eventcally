from dependency_injector.wiring import Provide, inject
from flask import current_app

from project.application.commands.report_event_command import ReportEventCommand
from project.application.message_bus import MessageBus
from project.application.queries import GetEventDetailQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.infrastructure.extensions import limiter
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.schemas import EventReportCreate, EventReportForm
from project.presentation.bff.routing import bff_route
from project.presentation.shared.query_results import result_or_404

EVENT_REPORT_RATE_LIMIT = "5/minute;20/hour"
EVENT_REPORT_RATE_LIMIT_SCOPE = "bff_event_report"


@bff_route(
    bff_public_bp,
    "/events/<int:id>/report-form",
    response=EventReportForm,
    summary="Get event report form",
)
@inject
def get_event_report_form(
    id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    event = result_or_404(query_bus.handle(GetEventDetailQuery(id=id)))
    return EventReportForm(event_id=event.id, event_name=event.name)


@bff_route(
    bff_public_bp,
    "/events/<int:id>/reports",
    method="POST",
    body=EventReportCreate,
    summary="Report event",
)
@inject
def report_event(
    id,
    body: EventReportCreate,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    with limiter.shared_limit(
        EVENT_REPORT_RATE_LIMIT, scope=EVENT_REPORT_RATE_LIMIT_SCOPE
    ):
        event = result_or_404(query_bus.handle(GetEventDetailQuery(id=id)))
        message_bus.handle_command(
            ReportEventCommand(
                event_id=event.id,
                actor=current_app.container.context.context_provider().current_actor,
                **body.model_dump(),
            )
        )
