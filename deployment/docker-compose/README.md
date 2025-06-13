# Deployment with Docker compose

## Configure

Copy example.env to .env and enter values.

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
