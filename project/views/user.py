from flask import render_template
from flask_security import auth_required

from project import app
from project.models import AdminUnitInvitation
from project.views.utils import get_invitation_access_result


@app.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html")


@app.route("/user/organization-invitations/<int:id>")
def user_organization_invitation(id):
    invitation = AdminUnitInvitation.query.get_or_404(id)
    result = get_invitation_access_result(invitation.email)

    if result:
        return result

    return render_template("user/organization_invitations.html")


@app.route("/user/organization-invitations")
@app.route("/user/organization-invitations/<path:path>")
@auth_required()
def user_organization_invitations(path=None):
    return render_template("user/organization_invitations.html")


@app.route("/user/favorite-events")
@auth_required()
def user_favorite_events():
    return render_template("user/favorite_events.html")
