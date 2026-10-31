# Deployment

## Docker

```sh
docker run -p 5000:5000 -e "DATABASE_URL=postgresql://postgres@localhost/eventcally" eventcally/eventcally:latest
```

### Verify the image

Release images carry a signed build provenance attestation and an SBOM:

```sh
gh attestation verify oci://docker.io/eventcally/eventcally:<version> --repo eventcally/eventcally
docker buildx imagetools inspect eventcally/eventcally:<version> --format '{{json .SBOM}}'
```

## Manual Installation

### Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Postgres with postgis

### Create database

```sh
psql -c 'create database eventcally;' -U postgres
```

### Install and run

```sh
uv sync --locked --no-dev
export DATABASE_URL='postgresql://postgres@localhost/eventcally'
uv run flask db upgrade
uv run flask data seed
uv run gunicorn -c gunicorn.conf.py main:app
```

## Scheduled/Cron jobs

Jobs that should run on a regular basis.

### Daily

```sh
flask cache clear-images
flask event update-recurring-dates
flask dump all
flask seo generate-sitemap
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

> **Tip:** To generate all of the secrets below (plus the Postgres/Redis
> passwords) at once, run [`deployment/generate-secrets.sh`](../deployment/generate-secrets.sh).
> It prints `KEY=VALUE` lines ready to paste into your `.env` and only needs
> `python3` and `openssl`.

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

| Variable                    | Function                                                                                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| CACHE_PATH                  | Absolute or relative path to root directory for dump and image caching. Default: project/tmp                                             |
| GOOGLE_MAPS_API_KEY         | Resolve addresses with Google Maps: API Key with Places API enabled                                                                      |
| PROXY_FIX_X_FOR             | Number of proxies in front of the app that append to `X-Forwarded-For`; the client IP (used by the rate limits) is taken from there. Default: 0 (header ignored) |
| LOG_FORMAT                  | Log line format of the app, Celery and gunicorn: `console` (readable) or `json` (one JSON object per line with `timestamp`, `level`, `logger`, `event`, `request_id`/`task_id` and the call's `extra` fields; exceptions in `exception`). `console` (multi-line tracebacks) is meant for local development and is set in `.flaskenv`. Default: json |
| LOG_LEVEL                   | Lowest level the app writes (`DEBUG`, `INFO`, `WARNING`, `ERROR`; the Celery worker uses its `--loglevel`). `GUNICORN_LOG_LEVEL` only sets gunicorn's own lines (boot, workers); app lines always go to stderr, also with `GUNICORN_ERROR_LOG`. Default: INFO |
| API_USAGE_LOG               | Log one record per `/api/` request (logger `eventcally.api_usage`, always at least INFO: credential, organization, app, user; no secrets; `LOG_FORMAT=json` writes it as one JSON line). Default: True |
| FEATURE_FLAGS                | Comma-separated list of opt-out feature tokens, see below. Default: empty (all features enabled). Unknown tokens are ignored.                |

#### Feature flag tokens

Opt-out semantics: listing a token *disables* that feature. The derived
`FEATURE_*_ENABLED` config keys are not read from the environment — set `FEATURE_FLAGS`
instead.

| Token                            | Effect                                                                                                                                                                                                                  |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ApiDeprecatedEndpointsDisabled` | Hides the deprecated `/api/v1` routes and methods (marked `deprecated` in Swagger, e.g. `/event-reference-requests/<id>`, PUT/PATCH/DELETE `/events/<id>`) from routing and Swagger, to test that clients no longer use them |

Retired tokens (`ApiEventDateDisabled`,
`ReferencedEventChangedDetailsDisabled`, …) are ignored.

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
