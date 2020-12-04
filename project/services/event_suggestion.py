from project import db
from project.models import EventReviewStatus, EventSuggestion
from sqlalchemy import and_


def insert_event_suggestion(event_suggestion):
    event_suggestion.review_status = EventReviewStatus.inbox
    db.session.add(event_suggestion)


def get_event_reviews_badge_query(admin_unit):
    return EventSuggestion.query.filter(
        and_(
            EventSuggestion.admin_unit_id == admin_unit.id,
            EventSuggestion.review_status == EventReviewStatus.inbox,
        )
    )


def get_event_reviews_query(admin_unit):
    return EventSuggestion.query.filter(EventSuggestion.admin_unit_id == admin_unit.id)
