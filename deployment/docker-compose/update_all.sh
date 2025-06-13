#!/bin/bash
set -e

docker compose stop web worker scheduler
docker compose exec db-backup /backup.sh
docker compose pull
docker compose up --detach web
docker compose exec web flask db upgrade
docker compose exec web flask data seed
docker compose up --detach