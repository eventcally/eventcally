# Deployment

## Automatic Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Docker

```sh
docker run -p 5000:5000 -e "DATABASE_URL=postgresql://postgres@localhost/eventcally" eventcally/eventcally:latest
```

## Manual Installation

### Requirements

- Python 3.9
- pip
- Postgres with postgis

### Create database

```sh
psql -c 'create database eventcally;' -U postgres
```

### Install and run

```sh
python3 -m venv env
source env/bin/activate
(env) pip install -r requirements.txt
(env) export DATABASE_URL='postgresql://postgres@localhost/eventcally'
(env) flask db upgrade
(env) gunicorn -c gunicorn.conf.py project:app
```

## Scheduled/Cron jobs

Jobs that should run on a regular basis.

### Daily

```sh
flask cache clear-images
flask event update-recurring-dates
flask dump all
flask seo generate-sitemap --pinggoogle
flask seo generate-robots-txt
```

## Administration

### Users

```sh
flask user add-admin-roles super@hero.com
```

### Worker active tasks

```sh
celery -A project.celery inspect active
```

## Configuration

Create `.env` file in the root directory or pass as environment variables.

### Security

| Variable               | Function                                                                                                                                                                           |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SECRET_KEY             | A secret key for verifying the integrity of signed cookies. Generate a nice key using `python3 -c "import secrets; print(secrets.token_urlsafe())"`.                               |
| SECURITY_PASSWORD_HASH | Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt. Generate a good salt using: `python3 -c "import secrets; print(secrets.SystemRandom().getrandbits(128))"`. |
| JWT_PRIVATE_KEY        | Private key for JWT (see "Generate JWT Keys for OIDC/OAuth")                                                                                                                       |
| JWT_PUBLIC_JWKS        | Public JWKS (see "Generate JWT Keys for OIDC/OAuth")                                                                                                                               |

### Send notifications via Mail

| Variable            | Function                                   |
| ------------------- | ------------------------------------------ |
| MAIL_DEFAULT_SENDER | see <https://pythonhosted.org/Flask-Mail/> |
| MAIL_PASSWORD       | "                                          |
| MAIL_PORT           | "                                          |
| MAIL_SERVER         | "                                          |
| MAIL_USERNAME       | "                                          |

### Misc

| Variable            | Function                                                                                     |
| ------------------- | -------------------------------------------------------------------------------------------- |
| CACHE_PATH          | Absolute or relative path to root directory for dump and image caching. Default: project/tmp |
| GOOGLE_MAPS_API_KEY | Resolve addresses with Google Maps: API Key with Places API enabled                          |

## Generate JWT Keys for OIDC/OAuth

```sh
openssl genrsa -out jwt-private.pem 2048
openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem
npm install -g pem-jwk
pem-jwk jwt-public.pem | jq '{kid: "default", kty: .kty , use: "sig", alg: "RS256", n: .n , e: .e }' > jwt-public.jwk
cat jwt-public.jwk | jq '{keys: [.]}' > jwt-public.jwks
```

Print environment variable JWT_PRIVATE_KEY:

```sh
awk '{printf "%s\\n", $0}' jwt-private.pem
```

Print environment variable JWT_PUBLIC_JWKS:

```sh
cat jwt-public.jwks | jq -r "(.|tojson)"
```
