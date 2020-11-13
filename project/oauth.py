from flask import flash
from flask_security import current_user, login_user
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from project.models import User, OAuth
from project import db, user_datastore
from flask_babelex import gettext

blueprint = make_google_blueprint(
    scope=["profile", "email"],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user),
)


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return False

    info = resp.json()
    user_id = info["id"]

    # Find this OAuth token in the database, or create it
    oauth = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id).first()
    if oauth is None:
        oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)

    if oauth.user:
        login_user(oauth.user, authn_via=["google"])
        user_datastore.commit()
        flash(gettext("Successfully signed in."), 'success')

    else:
        # Create a new local user account for this user
        user = user_datastore.create_user(email=info["email"])
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        login_user(user, authn_via=["google"])
        user_datastore.commit()
        flash(gettext("Successfully signed in."), 'success')

    # Disable Flask-Dance's default behavior for saving the OAuth token
    return False


# notify on OAuth provider error
@oauth_error.connect_via(blueprint)
def google_error(blueprint, message, response):
    msg = "OAuth error from {name}! message={message} response={response}".format(
        name=blueprint.name, message=message, response=response
    )
    flash(msg, category="error")
