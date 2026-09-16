from flask_babel import gettext


def get_success_text_for_request_creation(admin_unit_name: str, verified: bool) -> str:
    if verified:
        return gettext(
            "%(organization)s accepted your reference request",
            organization=admin_unit_name,
        )

    return gettext(
        "Reference request to %(organization)s successfully created. You will be notified after the other organization reviews the event.",
        organization=admin_unit_name,
    )
