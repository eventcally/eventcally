#!/usr/bin/env bash
# Runs the pytest-split suite as N parallel groups, each against its own database and
# Redis index, then combines coverage. Meant to run inside the `pytest` service of
# docker-compose.test.yml, which supplies TEST_DB_ADMIN_URL / TEST_DB_HOST /
# TEST_REDIS_HOST / TEST_LIMITER_REDIS_HOST.
set -euo pipefail

# Cores visible to this container, capped to what a container CPU quota (not just
# VM/host core count) actually allows -- nproc alone over-reports under a fractional
# `--cpus` cgroup quota. Also capped at 15: Redis only has 16 logical databases
# (0-15, with 0 reserved), so a many-core CI runner mustn't auto-pick a SPLITS that
# trips the check below on its own.
detect_cpus() {
    local n quota period q
    n="$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"

    if [ -r /sys/fs/cgroup/cpu.max ]; then # cgroup v2
        read -r quota period </sys/fs/cgroup/cpu.max
        if [ "$quota" != "max" ]; then
            q=$((quota / period))
            if [ "$q" -ge 1 ] && [ "$q" -lt "$n" ]; then
                n="$q"
            fi
        fi
    elif [ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]; then # cgroup v1
        quota="$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)"
        period="$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)"
        if [ "$quota" -gt 0 ]; then
            q=$((quota / period))
            if [ "$q" -ge 1 ] && [ "$q" -lt "$n" ]; then
                n="$q"
            fi
        fi
    fi

    if [ "$n" -gt 15 ]; then
        n=15
    fi

    echo "$n"
}

SPLITS="${SPLITS:-$(detect_cpus)}"
GROUP=""
NO_COV=0
EXTRA_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
    --splits)
        SPLITS="$2"
        shift 2
        ;;
    --group)
        GROUP="$2"
        shift 2
        ;;
    --no-cov)
        NO_COV=1
        shift
        ;;
    --)
        shift
        EXTRA_ARGS=("$@")
        break
        ;;
    *)
        echo "unknown argument: $1" >&2
        exit 1
        ;;
    esac
done

# Redis ships 16 logical databases (0-15); index 0 is reserved for anything not
# opted into per-group isolation, so groups can only use 1-15.
if [ "$SPLITS" -gt 15 ]; then
    echo "SPLITS=$SPLITS exceeds 15 -- a single Redis instance only has 16 logical" \
        "databases (0-15, with 0 reserved). Use separate Redis hosts above this." >&2
    exit 1
fi

rm -f .coverage .coverage.*

run_group() {
    local group="$1"
    COVERAGE_FILE=".coverage.${group}" \
        TEST_DATABASE_URL="postgresql://eventcally:pass@${TEST_DB_HOST}:5432/eventcally_tests_${group}" \
        TEST_REDIS_URL="redis://default:pass@${TEST_REDIS_HOST}:6379/${group}" \
        TEST_LIMITER_REDIS_URL="redis://default:pass@${TEST_LIMITER_REDIS_HOST}:6379/${group}" \
        pytest --cov=project --splits "$SPLITS" --group "$group" "${EXTRA_ARGS[@]}"
}

if [ -n "$GROUP" ]; then
    python .scripts/create_test_databases.py --groups "$GROUP"
    run_group "$GROUP"
    exit $?
fi

python .scripts/create_test_databases.py --splits "$SPLITS"

PIDS=()
for i in $(seq 1 "$SPLITS"); do
    run_group "$i" &
    PIDS+=("$!")
done

trap 'kill "${PIDS[@]}" 2>/dev/null' SIGINT

FAILED=0
for pid in "${PIDS[@]}"; do
    wait "$pid" || FAILED=1
done

if [ "$NO_COV" -eq 1 ]; then
    exit "$FAILED"
fi

coverage combine
coverage html
coverage report --precision=2 --fail-under=100

exit "$FAILED"
