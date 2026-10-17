#!/usr/bin/env bash
# Runs the Playwright e2e suite in Docker: PostGIS service, throwaway database, app on
# :5000 and Chromium all live in containers; no host Node, Python or Postgres needed.
# Arguments go to `playwright test`; `--project desktop` is the default.
#
#   .scripts/run_e2e.sh                                   # whole suite
#   .scripts/run_e2e.sh e2e/tests/event.spec.js           # one spec
#   .scripts/run_e2e.sh -g "create event" --project mobile
#   .scripts/run_e2e.sh --shard=1/3 --reporter=line
#   .scripts/run_e2e.sh --down                            # stop the services
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE=(docker compose -f docker-compose.test.yml)

if [ "${1:-}" = "--down" ]; then
    "${COMPOSE[@]}" down
    exit 0
fi

"${COMPOSE[@]}" up -d --wait db
"${COMPOSE[@]}" run --rm e2e .scripts/run_e2e_inner.sh "$@"
