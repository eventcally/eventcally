from dependency_injector.wiring import Provide, inject
from flask import abort, redirect, render_template, url_for
from flask_security import auth_required

from project.application.queries import GetOrganizationInvitationRecipientQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.views.main_blueprint import main_bp
from project.views.utils import get_invitation_access_result


@main_bp.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html")


@main_bp.route("/user/organization-invitations/<int:id>")
@inject
def user_organization_invitation(
    id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    # Endpunkt erforderlich, weil Nutzer noch nicht registriert sein können
    email = query_bus.handle(GetOrganizationInvitationRecipientQuery(id=id))

    if email is None:
        abort(404)

    result = get_invitation_access_result(email)

    if result:
        return result

    return redirect(
        url_for(
            "user.organization_invitation_negotiate",
            organization_invitation_id=id,
        )
    )
