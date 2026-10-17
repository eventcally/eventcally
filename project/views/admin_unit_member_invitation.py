from dependency_injector.wiring import Provide, inject
from flask import abort, redirect, url_for

from project.application.queries import GetMemberInvitationRecipientQuery
from project.application.query_bus import QueryBus
from project.container import Application
from project.views.main_blueprint import main_bp
from project.views.utils import get_invitation_access_result


@main_bp.route("/invitations/<int:id>", methods=("GET", "POST"))
@inject
def admin_unit_member_invitation(
    id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]
):
    # Endpunkt erforderlich, weil Nutzer noch nicht registriert sein können
    email = query_bus.handle(GetMemberInvitationRecipientQuery(id=id))

    if email is None:
        abort(404)

    result = get_invitation_access_result(email)

    if result:
        return result

    return redirect(
        url_for(
            "user.organization_member_invitation_negotiate",
            organization_member_invitation_id=id,
        )
    )
