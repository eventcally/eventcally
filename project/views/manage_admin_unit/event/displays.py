from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import (
    BoolProp,
    DateProp,
    EventCategoryListProp,
    EventDateStartProp,
    EventPlaceProp,
    EventStatusProp,
    IntProp,
    PublicStatusProp,
    StringProp,
)


class ListDisplay(BaseDisplay):
    main_index = 3
    min_start_definition = EventDateStartProp(lazy_gettext("Start"))
    is_recurring = BoolProp(lazy_gettext("Recurring event"), icon="fas fa-history")
    number_of_dates = IntProp(lazy_gettext("Event dates"), icon="fa fa-calendar-alt")
    name = StringProp(lazy_gettext("Name"))
    organizer = StringProp(lazy_gettext("Organizer"), keypath="organizer.name")
    event_place = EventPlaceProp(lazy_gettext("Place"))
    categories = EventCategoryListProp(lazy_gettext("Categories"))
    tags = StringProp(lazy_gettext("Tags"))
    status = EventStatusProp(lazy_gettext("Status"))
    public_status = PublicStatusProp(lazy_gettext("Public status"))
    photo = BoolProp(lazy_gettext("Photo"), icon="fa fa-image")
    number_of_references = IntProp(lazy_gettext("References"), icon="fa fa-share")
    number_of_reference_requests = IntProp(
        lazy_gettext("Reference requests"), icon="fa fa-question"
    )
    last_modified_at = DateProp(lazy_gettext("Last modified at"), icon="fa fa-save")
