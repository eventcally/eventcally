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
