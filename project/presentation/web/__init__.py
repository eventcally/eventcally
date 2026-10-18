from flask import Flask


def init_web(app: Flask):
    """Initialize the server-rendered web channel with the Flask app instance.

    Registers the blueprints (which pull in all views), error
    handlers, Jinja filters, Flask-Admin and the sign-up signal handler. Request hooks
    (`project.presentation.web.requests.init_requests`) are registered by the caller
    afterwards, because their order relative to other `before_request` hooks matters.
    """
    from flask_security import user_registered

    from project.domain.errors.unauthorized_error import UnauthorizedError
    from project.infrastructure.extensions import db
    from project.presentation.shared.i10n import get_locale_from_request
    from project.presentation.web.jinja_filters import init_jinja_filters
    from project.presentation.web.views.admin_blueprint import admin_bp
    from project.presentation.web.views.flask_admin import init_admin
    from project.presentation.web.views.main_blueprint import main_bp
    from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
    from project.presentation.web.views.manage_blueprint import manage_bp
    from project.presentation.web.views.user_blueprint import user_bp

    @user_registered.connect_via(app)
    def user_registered_sighandler(
        sender, user, confirm_token, confirmation_token, form_data
    ):
        if "accept_tos" in form_data and form_data["accept_tos"]:
            from project.infrastructure.user_datastore import set_user_accepted_tos

            set_user_accepted_tos(user)
            db.session.commit()

        if not user.locale:
            user.locale = get_locale_from_request()
            db.session.commit()

    app.register_blueprint(admin_bp)
    app.register_blueprint(manage_bp)
    app.register_blueprint(manage_admin_unit_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(main_bp)

    # Query handlers authorize the actor themselves; map their refusal to 401 for
    # views. API routes are handled by `RestApi.handle_error` first.
    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(error):
        from werkzeug.exceptions import Unauthorized

        return Unauthorized()

    init_jinja_filters(app)
    init_admin(app)
