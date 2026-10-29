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
