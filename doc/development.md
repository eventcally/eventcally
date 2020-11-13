# Development

## Tests

### Create test database

```sh
psql -c 'create database gsevpt_tests;' -U postgres
psql -c 'create extension postgis;' -d gsevpt_tests -U postgres
```

### Run tests

```sh
pytest
```

## Database

### Create new revision

```sh
python manage.py db migrate
```

### Upgrade database

```sh
python manage.py db upgrade
```

## i18n

<https://pythonhosted.org/Flask-BabelEx/>

### Init

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel init -i messages.pot -d app/translations -l de
```

### Extract new msgid's and merge into *.po files

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel update -i messages.pot -d app/translations
```

#### Compile after translation is done

```sh
pybabel compile -d app/translations
```
