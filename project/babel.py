def babel_extract(fileobj, keywords, comment_tags, options):
    """Extract messages.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    result = list()

    def _add_key(key, comment=""):
        result.append(
            (
                1,
                "",
                key,
                [comment],
            )
        )

    def _add_model(model_class):
        if not model_class:
            return

        _add_key(model_class.__display_name__)
        _add_key(model_class.__display_name_plural__)

    def _add_enum(enum_class):
        # get_localized_enum_name() builds "<EnumName>.<member>" at runtime, so
        # the extractor cannot see those keys in the source. Enums rendered that
        # way are listed here instead of relying on an incidental lazy_gettext()
        # elsewhere -- e.g. the review forms, which only offer the members a
        # reviewer may pick, never the pending `inbox` state the pills show.
        for member in enum_class:
            _add_key(f"{enum_class.__name__}.{member.name}")

    # Importing the models registers every mapper. Extraction runs under a bare
    # `pybabel` process, so there is no application to borrow a context from --
    # and none is needed: __display_name__ and __display_name_plural__ are plain
    # attributes assigned by CustomModel.__init_subclass__ at class definition
    # time, not lazily evaluated translations.
    import project.models  # noqa: F401
    from project.extensions import db
    from project.models import (
        AdminUnitVerificationRequestReviewStatus,
        EventReferenceRequestReviewStatus,
    )

    for mapper in db.Model.registry.mappers:
        _add_model(mapper.class_)

    _add_enum(EventReferenceRequestReviewStatus)
    _add_enum(AdminUnitVerificationRequestReviewStatus)

    return result
