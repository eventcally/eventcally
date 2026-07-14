#!/bin/bash
set -euo pipefail
source .env

DUMP_FILE="${1:-}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

if [ -z "$DUMP_FILE" ]; then
  echo "Usage: $0 <dump-file.sql.gz>"
  exit 1
fi

if [ ! -f "$DUMP_FILE" ]; then
  echo "Dump file not found: $DUMP_FILE"
  exit 1
fi

echo "Stopping stack to release database connections..."
docker compose -f "$COMPOSE_FILE" stop

echo "Starting db service..."
docker compose -f "$COMPOSE_FILE" up -d db

echo "Waiting for db to be healthy..."
until docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER}" 2>/dev/null; do
  sleep 2
done

echo "Dropping and recreating database..."
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "${POSTGRES_USER}" -d postgres \
  -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" \
  -c "CREATE DATABASE ${POSTGRES_DB} WITH ENCODING 'UTF8';"

echo "Restoring from $DUMP_FILE..."
gunzip -c "$DUMP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

echo "Done. Database restored from $DUMP_FILE."
