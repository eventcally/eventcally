# Deployment with Docker compose

## Configure

Copy example.env to .env and enter values.

## Initialize

```sh
./init.sh
```

## Start

```sh
docker compose up --force-recreate --detach
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
