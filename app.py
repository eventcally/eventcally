import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, current_user, auth_required, hash_password, SQLAlchemySessionUserDatastore

# Create app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

# Generate a nice key using secrets.token_urlsafe()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')

# create db
db = SQLAlchemy(app)

# Setup Flask-Security
# Define models
from models import User, Role
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
@app.before_first_request
def create_user():
    admin_role = user_datastore.find_or_create_role("admin", permissions=["user_create"])

    admin_user = user_datastore.find_user(email="grams.daniel@gmail.com")
    if admin_user is None:
        admin_user = user_datastore.create_user(email="grams.daniel@gmail.com", password=hash_password("password"))

    user_datastore.add_role_to_user(admin_user, admin_role)

    normal_user = user_datastore.find_user(email="normal.user@gmail.com")
    if normal_user is None:
        normal_user = user_datastore.create_user(email="normal.user@gmail.com", password=hash_password("password"))

    db.session.commit()

# Views
@app.route("/")
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()