#!/bin/sh
set -e

CERT_DIR="${CERT_DIR:-/certs}"
TLS_CERT="${TLS_CERT:-$CERT_DIR/server.crt}"
TLS_KEY="${TLS_KEY:-$CERT_DIR/server.key}"

mkdir -p "$CERT_DIR" "${REPORTS_DIR:-/reports}"

# Generate a self-signed certificate on first boot (ephemeral storage is fine).
if [ ! -f "$TLS_CERT" ] || [ ! -f "$TLS_KEY" ]; then
    echo "[entrypoint] generating self-signed certificate for CN=${CERT_CN:-localhost}"
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$TLS_KEY" -out "$TLS_CERT" \
        -days "${CERT_DAYS:-365}" -subj "/CN=${CERT_CN:-localhost}" >/dev/null 2>&1
fi

export TLS_CERT TLS_KEY
exec python3 /app/server.py
