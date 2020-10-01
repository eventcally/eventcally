from app import app
from utils import get_event_category_name, get_localized_enum_name
from urllib.parse import quote_plus
import os

def env_override(value, key):
  return os.getenv(key, value)

app.jinja_env.filters['event_category_name'] = lambda u: get_event_category_name(u)
app.jinja_env.filters['loc_enum'] = lambda u: get_localized_enum_name(u)
app.jinja_env.filters['env_override'] = env_override
app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)