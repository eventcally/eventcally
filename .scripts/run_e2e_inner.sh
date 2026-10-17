#!/usr/bin/env bash
# Runs inside the `e2e` container of docker-compose.test.yml: creates a throwaway
# database, starts the app on :5000 and runs the Playwright suite against it. Every
# spec truncates all tables, hence the dedicated database.
set -euo pipefail

DB_NAME="eventcally_e2e"
PSQL_ADMIN=(psql "$E2E_DB_ADMIN_URL" -v ON_ERROR_STOP=1 -q)

"${PSQL_ADMIN[@]}" -c "drop database if exists ${DB_NAME};" -c "create database ${DB_NAME};"
"${PSQL_ADMIN[@]}" -d "${E2E_DB_ADMIN_URL%/*}/${DB_NAME}" -c "create extension postgis;"

export DATABASE_URL="${E2E_DB_ADMIN_URL%/*}/${DB_NAME}"
export TESTING=1
export AUTHLIB_INSECURE_TRANSPORT=1
export BASE_URL="http://127.0.0.1:5000"

# Throwaway signing key for the OAuth specs (CI uses a fixed one).
eval "$(python - <<'PY'
import shlex
from authlib.jose import JsonWebKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
pem = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption(),
).decode()
jwk = JsonWebKey.import_key(
    key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode(),
    {"kid": "default", "use": "sig", "alg": "RS256"},
).as_dict()
print("export JWT_PRIVATE_KEY=" + shlex.quote(pem))
print("export JWT_PUBLIC_JWKS=" + shlex.quote(json.dumps({"keys": [jwk]})))
PY
)"

flask test create-all
flask test seed
gunicorn -b 127.0.0.1:5000 -w 1 main:app --daemon --log-file /tmp/gunicorn.log

for _ in $(seq 1 60); do
    curl --silent --fail --output /dev/null "$BASE_URL" && break
    sleep 1
done
curl --silent --fail --output /dev/null "$BASE_URL" || { cat /tmp/gunicorn.log; exit 1; }

# Default to the desktop project; pass `--project mobile` (or anything else) to override.
args=("$@")
case " ${args[*]:-} " in *" --project"*) ;; *) args=("${args[@]}" --project desktop) ;; esac

exec playwright test "${args[@]}"
