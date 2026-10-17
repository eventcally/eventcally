from sqlalchemy import func
from sqlalchemy.sql.operators import op


def create_tsvector(*args):
    field, weight = args[0]
    exp = func.setweight(func.to_tsvector("german", func.coalesce(field, "")), weight)
    for field, weight in args[1:]:
        exp = op(
            exp,
            "||",
            func.setweight(
                func.to_tsvector("german", func.coalesce(field, "")), weight
            ),
        )
    return exp


def sanitize_allday_instance(instance):
    from project.domain.dateutils import sanitize_allday_instance as domain_sanitize

    domain_sanitize(instance)
