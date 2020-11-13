from project.models import EventReviewStatus, EventSuggestion
from sqlalchemy import and_

def get_event_reviews_badge_query(admin_unit):
    return EventSuggestion.query.filter(and_(EventSuggestion.admin_unit_id == admin_unit.id, EventSuggestion.review_status == EventReviewStatus.inbox))

def get_event_reviews_query(admin_unit):
    return EventSuggestion.query.filter(EventSuggestion.admin_unit_id == admin_unit.id)

