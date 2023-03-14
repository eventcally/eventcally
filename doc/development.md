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

<https://pythonhosted.org/Flask-BabelEx/>

### Init

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel init -i messages.pot -d project/translations -l de
```

### Add locale

```sh
pybabel init -i messages.pot -d project/translations -l en
```

### Extract new msgid's and merge into \*.po files

```sh
pybabel extract -F babel.cfg -o messages.pot . && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . && pybabel update -N -i messages.pot -d project/translations
```

#### Compile after translation is done

```sh
pybabel compile -d project/translations
```

## Docker

### Build image

```sh
docker build -t danielgrams/gsevpt:latest .
```

### Run container with existing postgres server

```sh
docker run -p 5000:5000 -e "DATABASE_URL=postgresql://postgres@localhost/gsevpt" "gsevpt:latest"
```

### Compose (including Postgres server)

```sh
docker-compose build && docker-compose up
```

## Celery

```sh
dotenv run celery -A project.celery purge
```
