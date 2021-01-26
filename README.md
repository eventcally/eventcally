# Goslar Event Prototype

 ![Tests](https://github.com/DanielGrams/gsevpt/workflows/Tests/badge.svg) [![codecov](https://codecov.io/gh/DanielGrams/gsevpt/branch/master/graph/badge.svg?token=66CLLWWV7Y)](https://codecov.io/gh/DanielGrams/gsevpt) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) ![Docker Pulls](https://img.shields.io/docker/pulls/danielgrams/gsevpt)

Website prototype using Python, Flask and Postgres.

## Automatic Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Docker

```sh
docker run -p 5000:5000 -e "DATABASE_URL=postgresql://postgres@localhost/gsevpt" danielgrams/gsevpt:latest
```

## Manual Installation

### Requirements

- Python 3.7
- pip
- Postgres with postgis

### Create database

```sh
psql -c 'create database gsevpt;' -U postgres
```

### Install and run

```sh
python3 -m venv venv
source venv/bin/activate
(venv) pip install -r requirements.txt
(venv) export DATABASE_URL='postgresql://postgres@localhost/gsevpt'
(venv) flask db upgrade
(venv) gunicorn -c gunicorn.conf.py --bind 0.0.0.0:5000 project:app
```

## Scheduled/Cron jobs

Jobs that should run on a regular basis.

### Daily

```sh
flask event update-recurring-dates
flask dump all
```

## Administration

```sh
flask user add-admin-roles super@hero.com
```

## Configuration

Create `.env` file in the root directory or pass as environment variables.

### Security

| Variable | Function |
| --- | --- |
| SECRET_KEY | A secret key for verifying the integrity of signed cookies. Generate a nice key using `python3 -c "import secrets; print(secrets.token_urlsafe())"`. |
| SECURITY_PASSWORD_HASH | Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt. Generate a good salt using: `python3 -c "import secrets; print(secrets.SystemRandom().getrandbits(128))"`. |

### Send notifications via Mail

| Variable | Function |
| --- | --- |
| MAIL_DEFAULT_SENDER | see <https://pythonhosted.org/Flask-Mail/> |
| MAIL_PASSWORD | " |
| MAIL_PORT | " |
| MAIL_SERVER | " |
| MAIL_USERNAME | " |

### Misc

| Variable | Function |
| --- | --- |
| CACHE_PATH | Absolute or relative path to root directory for dump and image caching. Default: tmp |
| GOOGLE_MAPS_API_KEY | Resolve addresses with Google Maps: API Key with Places API enabled |

## Development

[Development](doc/development.md)
