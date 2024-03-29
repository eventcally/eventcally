# Development

## Docker

### Compose (including dependencies)

```sh
docker-compose up --build
```

### Build image

```sh
docker build -t eventcally/eventcally:latest .
```

### Run container with existing postgres server

```sh
docker run -p 5000:5000 -e "DATABASE_URL=postgresql://postgres@host.docker.internal/eventcally" eventcally/eventcally:latest
```

## Tests

### Create test database

```sh
psql -c 'create database eventcally_tests;' -U postgres
psql -c 'create extension postgis;' -d eventcally_tests -U postgres
```

### Run tests

```sh
pytest
```

With coverage:

```sh
pytest --cov-report=html --cov=project
```

## Database

### Create new revision

```sh
flask db migrate
```

### Upgrade database

```sh
flask db upgrade
```

## i18n

<https://python-babel.github.io/flask-babel/>

### Init

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -o messages.pot . && pybabel init -i messages.pot -d project/translations -l de
```

### Add locale

```sh
pybabel init -i messages.pot -d project/translations -l en
```

### Extract new msgid's and merge into \*.po files

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -k dummy_gettext -o messages.pot . && pybabel update -N -i messages.pot -d project/translations
```

#### Compile after translation is done

```sh
pybabel compile -d project/translations
```

## Celery

```sh
dotenv run celery -A project.celery purge
```
