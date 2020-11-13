[![Build Status](https://travis-ci.com/DanielGrams/gsevpt.svg?branch=master)](https://travis-ci.com/DanielGrams/gsevpt)

# Goslar Event Prototype

Website prototype using Python, Flask and Postgres running on Heroku.

## Automatic Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

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
export DATABASE_URL="postgresql://postgres@localhost/gsevpt"
pip install -r requirements.txt
python manage.py db upgrade
flask run --host 0.0.0.0
```

## Configuration

Create `.env` file in the root directory or pass as environment variables.

### Security

| Variable | Function |
| --- | --- |
| SECRET_KEY | A secret key for verifying the integrity of signed cookies. Generate a nice key using secrets.token_urlsafe(). |
| SECURITY_PASSWORD_HASH | Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt. Generate a good salt using: secrets.SystemRandom().getrandbits(128). |

### Send notifications via Mail

| Variable | Function |
| --- | --- |
| MAIL_DEFAULT_SENDER | Send notifications via Mail, see <https://pythonhosted.org/Flask-Mail/> |
| MAIL_PASSWORD | " |
| MAIL_PORT | " |
| MAIL_SERVER | " |
| MAIL_USERNAME | " |

### Login with Google via OAuth

| Variable | Function |
| --- | --- |
| GOOGLE_OAUTH_CLIENT_ID | Client Id |
| GOOGLE_OAUTH_CLIENT_SECRET | Secret |

### Resolve addresses with Google Maps

| Variable | Function |
| --- | --- |
| GOOGLE_MAPS_API_KEY | API Key with Places API enabled |

## Development

[Development](doc/development.md)