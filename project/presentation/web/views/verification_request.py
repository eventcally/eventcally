from dependency_injector.wiring import Provide, inject
from flask import current_app, flash, g, redirect, render_template, url_for
from flask_babel import gettext
from flask_security import auth_required

from project.application.commands import RequestOrganizationVerificationCommand
from project.application.message_bus import MessageBus
from project.application.queries import (
    CanRequestVerificationQuery,
    GetOrganizationQuery,
    ListVerifierOrganizationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors import BaseError
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    page_request_from_request_args,
    result_or_404,
)
from project.presentation.web.forms.verification_request import (
    CreateAdminUnitVerificationRequestForm,
)
from project.presentation.web.views.main_blueprint import main_bp
from project.presentation.web.views.utils import (
    flash_errors,
    get_pagination_urls,
    handleBaseError,
    manage_required,
)


@main_bp.route(
    "/manage/admin_unit/<int:id>/verification_requests/outgoing/create/select"
)
@auth_required()
@manage_required("outgoing_organization_verification_requests:write")
@inject
def manage_organization_verification_requests_outgoing_create_select(
    id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    admin_unit = g.manage_admin_unit

    admin_units = query_bus.handle(
        ListVerifierOrganizationsQuery(
            postal_code=admin_unit.location.postalCode,
            page=page_request_from_request_args(),
        )
    )
    abort_if_page_out_of_range(admin_units)

    return render_template(
        "manage/verification_requests_outgoing_create_select.html",
        admin_unit=admin_unit,
        admin_units=admin_units.items,
        pagination=get_pagination_urls(admin_units, id=id),
    )


@main_bp.route(
    "/manage/admin_unit/<int:id>/verification_requests/outgoing/create/target/<int:target_id>",
    methods=("GET", "POST"),
)
@auth_required()
@manage_required("outgoing_organization_verification_requests:write")
@inject
def manage_organization_requests_outgoing_create(
    id,
    target_id,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    admin_unit = g.manage_admin_unit
    target_admin_unit = result_or_404(
        query_bus.handle(GetOrganizationQuery(id=target_id))
    )

    if not query_bus.handle(
        CanRequestVerificationQuery(
            source_admin_unit_id=admin_unit.id,
            target_admin_unit_id=target_admin_unit.id,
        )
    ):
        return redirect(
            url_for(
                "main.manage_organization_verification_requests_outgoing_create_select",
                id=admin_unit.id,
            )
        )

    form = CreateAdminUnitVerificationRequestForm()

    if form.validate_on_submit():
        try:
            cmd = RequestOrganizationVerificationCommand(
                actor=current_app.container.context.context_provider().current_actor,
                source_admin_unit_id=admin_unit.id,
                target_admin_unit_id=target_admin_unit.id,
            )
            message_bus.handle_command(cmd)
            msg = gettext(
                "Request successfully created. You will be notified after the other organization reviewed the request."
            )
            flash(msg, "success")
            return redirect(
                url_for(
                    "manage_admin_unit.outgoing_organization_verification_requests",
                    id=admin_unit.id,
                )
            )
        except BaseError as e:
            flash(handleBaseError(e), "danger")
    else:
        flash_errors(form)

    return render_template(
        "manage/verification_requests_outgoing_create.html",
        form=form,
        admin_unit=admin_unit,
        target_admin_unit=target_admin_unit,
    )
