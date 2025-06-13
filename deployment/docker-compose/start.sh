#!/bin/bash
set -e

docker compose up --detach web
docker compose exec web flask db upgrade
docker compose exec web flask data seed
docker compose up --detach