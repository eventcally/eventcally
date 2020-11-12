# Goslar Event Prototype

Website prototype using Python, Flask and Postgres running on Heroku.

## Setup

### Environment variables

Create `.env` file in the root directory and define the following variables:

```
DATABASE_URL=
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
OAUTHLIB_INSECURE_TRANSPORT=true
OAUTHLIB_RELAX_TOKEN_SCOPE=true
GOOGLE_MAPS_API_KEY=
```

### Install and run

```
pip install -r requirements.txt
flask run --host 0.0.0.0
```

## Tests

### Create test database

```
psql -c 'create database gsevpt_tests;' -U postgres && psql -c 'create extension postgis;' -d gsevpt_tests -U postgres
```

### Run tests

```
pytest
```


## Development

### Database

```
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```

#### Local development only

```
python manage.py db history
python manage.py db downgrade
// reset git: migrations/versions
python manage.py db migrate
python manage.py db upgrade
```

### Kill local detached server

```
lsof -i :5000
kill -9 PIDNUMBER
```

### i18n

<https://pythonhosted.org/Flask-BabelEx/>

#### Init

```
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel init -i messages.pot -d app/translations -l de
```

#### Neue msgid's scannen und in *.po mergen

```
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel update -i messages.pot -d app/translations
```

#### Nach dem Übersetzen

```
pybabel compile -d app/translations
```
