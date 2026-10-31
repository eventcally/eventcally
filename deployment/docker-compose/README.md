# Deployment with Docker compose

## Configure

Copy `.env.example` to `.env` and enter values.

```sh
cp .env.example .env
```

### Generate secrets

Generate all required secrets (`SECRET_KEY`, `SECURITY_PASSWORD_HASH`,
`JWT_PRIVATE_KEY`, `JWT_PUBLIC_JWKS`, and the Postgres/Redis passwords) and
append them to your `.env`:

```sh
../generate-secrets.sh >> .env
```

Then fill in the remaining non-secret values (`SERVER_NAME`, mail settings,
`GOOGLE_MAPS_API_KEY`, …). The script only needs `python3` and `openssl`.

### Behind an outer proxy

Rate limits key on the client IP, which the app takes from `X-Forwarded-For`.
`PROXY_FIX_X_FOR` is the number of proxies that append to that header: `1` for the
bundled nginx alone (default), `2` behind an outer proxy such as Plesk. Then also set
`HTTP_BIND=127.0.0.1`, so nobody can reach nginx directly and choose their own IP.

To check it: the gunicorn access log of the `web` container shows `X-Forwarded-For`
per request; it must hold `PROXY_FIX_X_FOR` entries, the client being the first of them
(e.g. `203.0.113.7, 172.24.0.1` for `2`).

## Logs

fluentd reads the logs of all containers on the host but keeps only those of the compose
project `FLUENTD_COMPOSE_PROJECT` (default `eventcally`, the `name` in `docker-compose.yml`;
set it when you start the stack with another `-p`). Docker adds the project label to each
log line (`x-logging` in `docker-compose.yml`); it applies to containers created after
the change, so recreate them with `docker compose up --detach`. It writes to
`FLUENTD_LOG_PATH`:

- `docker-error.*`: lines with an error level or worse. The app, Celery and gunicorn
  write JSON (`LOG_FORMAT=json`): their records have `level` `error` or `critical`,
  with `event`, `logger`, `request_id` (web) or `task_id`/`task_name` (Celery) and the
  traceback in `exception`. API usage records with a 5xx status have `level` `error`
  too. Lines that are not JSON (nginx, PostgreSQL, `LOG_FORMAT=console`) keep their
  text in `log` and count by it: `[error]`/`[critical]`, nginx `[crit]`/`[alert]`/
  `[emerg]`, PostgreSQL `FATAL:`/`PANIC:`. Find a request's lines by its
  `X-Request-ID`: `grep '"request_id":"<id>"' docker-error.*`.
- `api-usage.YYYYMMDD.log.gz`: one JSON record per API request (`API_USAGE_LOG`,
  default on; needs `LOG_FORMAT=json`): `timestamp`, `level` (`error` for a 5xx status), method, path, endpoint, status, duration, client IP (see above),
  user agent, the credential (`auth`: `oauth2`, `api_key` or `none`; token, client,
  app, installation or API key id) and the organization and user it belongs to,
  plus the `X-Request-ID` of the response. Tokens, API keys and secrets are never
  written; values of token-like query arguments (`access_token`, `client_secret`, …)
  are redacted. Each record carries the `project`. Read them with `zcat api-usage.*.gz`.

The API usage files are kept for `API_USAGE_LOG_RETENTION_DAYS` (default 90) days:
fluentd itself deletes older ones every hour. A day's file is written
shortly after the day ends (UTC); to check a setup, set `API_USAGE_LOG_TIMEKEY=60` and a
file appears about two minutes after the request.

`init.sh` copies `fluentd-custom.config` to `FLUENTD_CUSTOM_CONFIG_PATH`. After changing
it, copy it again and run `docker compose up --detach fluentd` (or `restart fluentd`).

## Initialize

```sh
./init.sh
```

## Start

```sh
./start.sh
```

## Update app

Adjust `WEB_TAG` in .env if necessary.

```sh
./update.sh
```

## Execute commands in web container

```sh
docker compose exec -it web /bin/sh
```

## Worker active tasks

```sh
docker compose exec -it worker celery -A project.celery inspect active
```
