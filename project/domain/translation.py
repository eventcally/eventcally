def dummy_gettext(message: str) -> str:
    """Mark ``message`` for extraction by ``pybabel`` without translating it.

    Domain and application code cannot depend on flask_babel. Errors carry the
    untranslated text, and the delivery layer translates it at runtime
    (see ``project/views/utils.py::handleBaseError``).
    """
    return message
