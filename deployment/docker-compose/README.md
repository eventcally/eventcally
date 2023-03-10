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

```sh
./update.sh
```
