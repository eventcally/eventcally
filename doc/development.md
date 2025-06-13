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
.scripts/translations/init.sh
```

### Add locale

```sh
.scripts/translations/add_locale.sh de
```

### Extract new msgid's and merge into \*.po files

```sh
.scripts/translations/extract.sh
```

#### Compile after translation is done

```sh
.scripts/translations/compile.sh
```

## Celery

```sh
dotenv run celery -A project.celery purge
```
