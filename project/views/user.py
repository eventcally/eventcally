from flask import redirect, render_template, url_for
from flask_security import auth_required

from project.models import AdminUnitInvitation
from project.views.main_blueprint import main_bp
from project.views.utils import get_invitation_access_result


@main_bp.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html")


@main_bp.route("/user/organization-invitations/<int:id>")
def user_organization_invitation(id):
    # Endpunkt erforderlich, weil Nutzer noch nicht registriert sein können
    invitation = AdminUnitInvitation.query.get_or_404(id)
    result = get_invitation_access_result(invitation.email)

    if result:
        return result

    return redirect(
        url_for(
            "user.organization_invitation_negotiate",
            organization_invitation_id=id,
        )
    )


@main_bp.route("/user/favorite-events")
@auth_required()
def user_favorite_events():
    return render_template("user/favorite_events.html")
