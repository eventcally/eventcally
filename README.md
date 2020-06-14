# Database

python manage.py db init
python manage.py db migrate
python manage.py db upgrade

## Developemt !!!
python manage.py db history
python manage.py db downgrade
// reset git: migrations/versions
python manage.py db migrate
python manage.py db upgrade

## Kill local detached server
lsof -i :5000
kill -9 PIDNUMBER

# i18n

https://pythonhosted.org/Flask-BabelEx/

## Init
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel init -i messages.pot -d translations -l de

## Neue msgid's scannen und in *.po mergen
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel update -i messages.pot -d translations

## Nach dem Übersetzen
pybabel compile -d translations
