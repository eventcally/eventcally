#!/usr/bin/env bash
#
# Generate all secrets required by EventCally (see doc/deployment.md).
#
# Prints KEY=VALUE lines ready to paste into your .env file:
#   POSTGRES_PASSWORD, REDIS_PASSWORD, LIMITER_REDIS_PASSWORD,
#   SECRET_KEY, SECURITY_PASSWORD_HASH, JWT_PRIVATE_KEY, JWT_PUBLIC_JWKS
#
# Requires: python3, openssl (no npm/pem-jwk/jq needed).
#
# Usage:
#   ./generate-secrets.sh                 # print secrets to stdout
#   ./generate-secrets.sh >> .env         # append to an .env file
#
set -euo pipefail

command -v python3 >/dev/null || { echo "error: python3 not found" >&2; exit 1; }
command -v openssl >/dev/null || { echo "error: openssl not found" >&2; exit 1; }

# URL-safe random password for Postgres / Redis services.
gen_password() {
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe())')"
SECURITY_PASSWORD_HASH="$(python3 -c 'import secrets; print(secrets.SystemRandom().getrandbits(128))')"
POSTGRES_PASSWORD="$(gen_password)"
REDIS_PASSWORD="$(gen_password)"
LIMITER_REDIS_PASSWORD="$(gen_password)"

# JWT RSA keypair for OIDC/OAuth.
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
openssl genrsa -out "$tmpdir/jwt-private.pem" 2048 2>/dev/null

# JWT_PRIVATE_KEY: PEM collapsed to a single line with literal "\n" separators.
JWT_PRIVATE_KEY="$(awk '{printf "%s\\n", $0}' "$tmpdir/jwt-private.pem")"

# JWT_PUBLIC_JWKS: build the public JWKS from the key's modulus + exponent
# (base64url-encoded), matching the format in doc/deployment.md.
modulus_hex="$(openssl rsa -in "$tmpdir/jwt-private.pem" -noout -modulus 2>/dev/null | sed 's/^Modulus=//')"
JWT_PUBLIC_JWKS="$(python3 - "$modulus_hex" <<'PY'
import base64, json, sys

modulus_hex = sys.argv[1]
n = base64.urlsafe_b64encode(bytes.fromhex(modulus_hex)).rstrip(b"=").decode()
# genrsa uses the standard public exponent 65537 (0x010001 -> "AQAB").
e = base64.urlsafe_b64encode((65537).to_bytes(3, "big")).rstrip(b"=").decode()
jwks = {
    "keys": [
        {"kid": "default", "kty": "RSA", "use": "sig", "alg": "RS256", "n": n, "e": e}
    ]
}
print(json.dumps(jwks, separators=(",", ":")))
PY
)"

cat <<EOF
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
LIMITER_REDIS_PASSWORD=$LIMITER_REDIS_PASSWORD
SECRET_KEY=$SECRET_KEY
SECURITY_PASSWORD_HASH=$SECURITY_PASSWORD_HASH
JWT_PRIVATE_KEY="$JWT_PRIVATE_KEY"
JWT_PUBLIC_JWKS='$JWT_PUBLIC_JWKS'
EOF
