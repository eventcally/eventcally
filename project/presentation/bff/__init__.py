from flask import Blueprint, Flask, jsonify
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from project.domain.errors import BaseError
from project.domain.errors.unauthorized_error import UnauthorizedError

bff_bp = Blueprint("bff", __name__, url_prefix="/bff")

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _error_response(name: str, message: str, code: int, **extra):
    from project.presentation.bff.schemas import ErrorResponse

    payload = ErrorResponse(name=name, message=message).model_dump(mode="json")
    payload.update(extra)
    return jsonify(payload), code


@bff_bp.before_request
def _require_session_user():
    # JSON clients never get Flask-Security's login redirect, whatever the Accept header.
    if current_user.is_anonymous:
        return _error_response("Unauthorized", "Authentication required.", 401)


@bff_bp.before_request
def _protect_unsafe_methods():
    from flask import request

    from project.infrastructure.extensions import csrf

    # CSRF is opt-in app-wide (WTF_CSRF_CHECK_DEFAULT = False).
    if request.method in _UNSAFE_METHODS:
        csrf.protect()


@bff_bp.errorhandler(ValidationError)
def _handle_validation_error(err: ValidationError):
    from project.presentation.bff.schemas import FieldError, ValidationErrorResponse

    errors = [
        FieldError(loc=[str(part) for part in e["loc"]], msg=e["msg"])
        for e in err.errors()
    ]
    payload = ValidationErrorResponse(
        name="Unprocessable Entity",
        message="The request was well-formed but was unable to be followed due to semantic errors.",
        errors=errors,
    )
    return jsonify(payload.model_dump(mode="json")), 422


@bff_bp.errorhandler(UnauthorizedError)
def _handle_unauthorized_error(err: UnauthorizedError):
    if current_user.is_anonymous:
        return _error_response("Unauthorized", err.message, 401)
    return _error_response("Forbidden", err.message, 403)


@bff_bp.errorhandler(IntegrityError)
def _handle_integrity_error(err: IntegrityError):
    from project.infrastructure.extensions import db

    try:
        db.session.rollback()
    except Exception:  # pragma: no cover
        pass

    return _error_response(
        "Integrity Error", "Action violates database integrity.", 400
    )


@bff_bp.errorhandler(BaseError)
def _handle_base_error(err: BaseError):
    return _error_response(err.__class__.__name__, err.message, 400)


@bff_bp.errorhandler(CSRFError)
def _handle_csrf_error(err: CSRFError):
    return _error_response(err.name, err.description, 400)


@bff_bp.errorhandler(HTTPException)
def _handle_http_exception(err: HTTPException):
    return _error_response(err.name, err.description or "", err.code or 500)


def _register_sub_blueprints():
    # Blueprints are module-level singletons shared by every app created in the
    # process (tests build many), so nesting is wired once at import time.
    from project.presentation.bff.admin import bff_admin_bp
    from project.presentation.bff.routing import set_parent

    set_parent(bff_admin_bp, bff_bp)
    bff_bp.register_blueprint(bff_admin_bp)


_register_sub_blueprints()


def init_bff(app: Flask):
    """Initialize the BFF channel: view-shaped JSON for the Vue frontends.

    Must run before the DI container is wired (it imports the route modules).
    """
    app.register_blueprint(bff_bp)
