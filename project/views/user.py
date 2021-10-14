from flask import redirect, render_template, url_for
from flask_security import auth_required, current_user

from project import app
from project.models import AdminUnitInvitation
from project.services.user import find_user_by_email


@app.route("/profile")
@auth_required()
def profile():
    return render_template("profile.html")


@app.route("/user/organization-invitations/<int:id>")
def user_organization_invitation(id):
    invitation = AdminUnitInvitation.query.get_or_404(id)

    # Wenn Email nicht als Nutzer vorhanden, dann direkt zu Registrierung
    if not find_user_by_email(invitation.email):
        return redirect(url_for("security.register"))

    if not current_user.is_authenticated:
        return app.login_manager.unauthorized()

    return render_template("user/organization_invitations.html")


@app.route("/user/organization-invitations")
@app.route("/user/organization-invitations/<path:path>")
@auth_required()
def user_organization_invitations(path=None):
    return render_template("user/organization_invitations.html")
