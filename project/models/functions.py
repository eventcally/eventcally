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
    if instance.allday:
        from project.dateutils import date_set_begin_of_day, date_set_end_of_day

        instance.start = date_set_begin_of_day(instance.start)

        if instance.end:
            instance.end = date_set_end_of_day(instance.end)
        else:
            instance.end = date_set_end_of_day(instance.start)
