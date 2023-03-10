set -e

docker compose pull web
docker compose stop web
docker compose run db-backup /backup.sh
docker compose up --detach --force-recreate web