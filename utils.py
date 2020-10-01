from flask_babelex import lazy_gettext

def get_event_category_name(category):
    return lazy_gettext('Event_' + category.name)

def get_localized_enum_name(enum):
    return lazy_gettext(enum.__class__.__name__ + '.' + enum.name)