#!/usr/bin/env bash
# Runs the pytest-split suite as N parallel groups, each against its own database and
# Redis index, then combines coverage. Meant to run inside the `pytest` service of
# docker-compose.test.yml, which supplies TEST_DB_ADMIN_URL / TEST_DB_HOST /
# TEST_REDIS_HOST / TEST_LIMITER_REDIS_HOST. CI overrides the defaults of
# TEST_DB_CREDENTIALS (eventcally:pass), TEST_REDIS_CREDENTIALS (default:pass; empty = no
# auth), TEST_REDIS_PORT and TEST_LIMITER_REDIS_PORT (both 6379).
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
SLICE=""
STORE_DURATIONS=0
SHARD=1
SHARDS=1
NO_REPORT=0
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
    --slice)
        # Comma-separated names from .scripts/test_slices.py (unit, infra, web, api, bff, misc)
        SLICE="$2"
        shift 2
        ;;
    --store-durations)
        STORE_DURATIONS=1
        shift
        ;;
    --shard)
        # 1-based; this invocation runs the global groups (SHARD-1)*SPLITS+1 .. SHARD*SPLITS
        SHARD="$2"
        shift 2
        ;;
    --shards)
        SHARDS="$2"
        shift 2
        ;;
    --no-report)
        # Combine coverage only: no html, no global gate, no slice check (CI gates elsewhere)
        NO_REPORT=1
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

if [ "$SHARD" -lt 1 ] || [ "$SHARD" -gt "$SHARDS" ]; then
    echo "--shard $SHARD is outside 1..$SHARDS (--shards)." >&2
    exit 1
fi

# pytest-split sees every group of every shard; databases are named by the global group,
# Redis indexes by the group's position within this shard (see run_group).
TOTAL_GROUPS=$((SHARDS * SPLITS))
FIRST_GROUP=$(((SHARD - 1) * SPLITS + 1))
LAST_GROUP=$((SHARD * SPLITS))

DB_CREDENTIALS="${TEST_DB_CREDENTIALS:-eventcally:pass}"
REDIS_CREDENTIALS="${TEST_REDIS_CREDENTIALS-default:pass}"
REDIS_AUTH=""
if [ -n "$REDIS_CREDENTIALS" ]; then
    REDIS_AUTH="${REDIS_CREDENTIALS}@"
fi
REDIS_PORT="${TEST_REDIS_PORT:-6379}"
LIMITER_REDIS_PORT="${TEST_LIMITER_REDIS_PORT:-6379}"

# Redis ships 16 logical databases (0-15); index 0 is reserved for anything not
# opted into per-group isolation, so groups can only use 1-15.
if [ "$SPLITS" -gt 15 ]; then
    echo "SPLITS=$SPLITS exceeds 15 -- a single Redis instance only has 16 logical" \
        "databases (0-15, with 0 reserved). Use separate Redis hosts above this." >&2
    exit 1
fi

if [ "$STORE_DURATIONS" -eq 1 ] && [ -n "$SLICE" ]; then
    echo "--store-durations needs the full suite; drop --slice." >&2
    exit 1
fi

# Test paths: tests/unit plus the paths of every selected slice, de-duplicated.
SLICE_PATHS=()
SLICE_NAMES=()
if [ -n "$SLICE" ]; then
    IFS=',' read -r -a SLICE_NAMES <<<"$SLICE"
    for name in "${SLICE_NAMES[@]}"; do
        while IFS= read -r path; do
            SLICE_PATHS+=("$path")
        done < <(python .scripts/test_slices.py tests "$name")
    done
    mapfile -t SLICE_PATHS < <(printf '%s\n' "${SLICE_PATHS[@]}" | awk '!seen[$0]++')
fi

# The slice check prints a table per slice and fails for an ENFORCED one under 100%.
check_slices() {
    local status=0 name
    for name in "${SLICE_NAMES[@]}"; do
        python .scripts/test_slices.py check --slice "$name" || status=1
    done
    return "$status"
}

rm -f .coverage .coverage.*

# Unit-only slice: no databases, no Redis, no splitting.
if [ -n "$SLICE" ] && [ "${SLICE_PATHS[*]}" = "tests/unit" ]; then
    FAILED=0
    pytest --cov=project --cov-context=test "${SLICE_PATHS[@]}" "${EXTRA_ARGS[@]}" || FAILED=1
    if [ "$NO_COV" -eq 0 ]; then
        check_slices || FAILED=1
    fi
    exit "$FAILED"
fi

run_group() {
    local group="$1"
    local redis_index=$(((group - 1) % SPLITS + 1))
    local durations=()
    if [ "$STORE_DURATIONS" -eq 1 ]; then
        durations=(--store-durations --durations-path ".test_durations.${group}")
    fi
    COVERAGE_FILE=".coverage.${group}" \
        TEST_DATABASE_URL="postgresql://${DB_CREDENTIALS}@${TEST_DB_HOST}:5432/eventcally_tests_${group}" \
        TEST_REDIS_URL="redis://${REDIS_AUTH}${TEST_REDIS_HOST}:${REDIS_PORT}/${redis_index}" \
        TEST_LIMITER_REDIS_URL="redis://${REDIS_AUTH}${TEST_LIMITER_REDIS_HOST}:${LIMITER_REDIS_PORT}/${redis_index}" \
        pytest --cov=project --cov-context=test --splits "$TOTAL_GROUPS" --group "$group" \
        --splitting-algorithm least_duration "${durations[@]}" "${SLICE_PATHS[@]}" "${EXTRA_ARGS[@]}"
}

if [ -n "$GROUP" ]; then
    python .scripts/create_test_databases.py --groups "$GROUP"
    run_group "$GROUP"
    exit $?
fi

python .scripts/create_test_databases.py --groups $(seq "$FIRST_GROUP" "$LAST_GROUP")

PIDS=()
for i in $(seq "$FIRST_GROUP" "$LAST_GROUP"); do
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

if [ "$STORE_DURATIONS" -eq 1 ]; then
    python - <<'PY'
import glob
import json

durations = {}
for path in sorted(glob.glob(".test_durations.*")):
    with open(path) as f:
        durations.update(json.load(f))

with open(".test_durations", "w") as f:
    json.dump(durations, f, sort_keys=True, indent=4)
    f.write("\n")
PY
    rm -f .test_durations.*
fi

if [ "$NO_REPORT" -eq 1 ]; then
    exit "$FAILED"
fi

coverage html

if [ -n "$SLICE" ]; then
    # A slice run only covers its own part of project/, so the global gate does not apply.
    check_slices || FAILED=1
else
    coverage report --precision=2 --fail-under=100 || FAILED=1
fi

exit "$FAILED"
