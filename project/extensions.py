"""Flask extensions initialized without app binding.

These extension instances are created here without being bound to a Flask app.
They will be initialized with an app using init_app() in the application factory.
"""

from flask_babel import Babel
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import MetaData

from project.base_model import CustomModel

# SQLAlchemy naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)

# Extension instances (not bound to app yet)
# Note: Flask-Gzip doesn't support init_app pattern, so it's created directly in create_app()
babel = Babel()
cors = CORS()
csrf = CSRFProtect()
mail = Mail()
db = SQLAlchemy(model_class=CustomModel, metadata=metadata)
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
security = Security()
