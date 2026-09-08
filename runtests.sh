#!/usr/bin/env bash
# The one command everyone types: brings up the test db/redis/limiter_redis services and
# runs the parallel split suite for them inside the pytest container. No host Postgres, no
# host Redis, no venv required.
set -euo pipefail

COMPOSE=(docker compose -f docker-compose.test.yml)

if [ "${1:-}" = "--down" ]; then
    "${COMPOSE[@]}" down
    exit 0
fi

"${COMPOSE[@]}" up -d --wait db redis limiter_redis
"${COMPOSE[@]}" run --rm pytest .scripts/run_tests.sh "$@"
