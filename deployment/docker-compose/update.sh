set -e

docker compose pull web
docker compose stop web worker scheduler
docker compose exec db-backup /backup.sh
docker compose up --detach --force-recreate web worker scheduler