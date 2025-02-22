from flask import redirect, url_for

from project import app
from project.models import AdminUnitMemberInvitation
from project.views.utils import get_invitation_access_result


@app.route("/invitations/<int:id>", methods=("GET", "POST"))
def admin_unit_member_invitation(id):
    # Endpunkt erforderlich, weil Nutzer noch nicht registriert sein können
    invitation = AdminUnitMemberInvitation.query.get_or_404(id)
    result = get_invitation_access_result(invitation.email)

    if result:
        return result

    return redirect(
        url_for(
            "user.organization_member_invitation_negotiate",
            organization_member_invitation_id=id,
        )
    )
