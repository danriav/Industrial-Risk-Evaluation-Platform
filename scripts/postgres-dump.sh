#!/bin/sh
set -eu

: "${POSTGRES_HOST:=database}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"
: "${BACKUP_DIR:=/backups}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_file="${BACKUP_DIR}/${POSTGRES_DB}_${timestamp}.dump"
temp_file="${output_file}.tmp"

mkdir -p "${BACKUP_DIR}"
rm -f "${temp_file}"

pg_dump \
  --host="${POSTGRES_HOST}" \
  --port="${POSTGRES_PORT}" \
  --username="${POSTGRES_USER}" \
  --dbname="${POSTGRES_DB}" \
  --format=custom \
  --no-owner \
  --no-acl \
  --file="${temp_file}"

mv "${temp_file}" "${output_file}"

echo "Database backup created: ${output_file}"
