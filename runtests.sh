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

# --changed [BASE] -> --slice <slices touched by the diff against BASE>. Resolved here on the
# host: it needs git, which the pytest image may not have. BASE defaults to origin/main.
if [ "${1:-}" = "--changed" ]; then
    shift
    BASE="origin/main"
    if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then
        BASE="$1"
        shift
    fi
    CHANGED="$(python3 .scripts/test_slices.py changed "$BASE" | paste -sd, -)"
    if [ -z "$CHANGED" ]; then
        echo "No slice owns the changed files; nothing to run."
        exit 0
    fi
    echo "Changed slices: $CHANGED"
    set -- --slice "$CHANGED" "$@"
fi

"${COMPOSE[@]}" up -d --wait db redis limiter_redis
"${COMPOSE[@]}" run --rm pytest .scripts/run_tests.sh "$@"
