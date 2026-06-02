#!/bin/sh
set -eu

: "${BACKUP_INTERVAL_SECONDS:=86400}"
: "${BACKUP_RETENTION_DAYS:=14}"
: "${BACKUP_DIR:=/backups}"
: "${BACKUP_RETRY_SECONDS:=10}"
: "${BACKUP_MAX_ATTEMPTS:=12}"

run_backup_with_retry() {
  attempt=1
  while [ "${attempt}" -le "${BACKUP_MAX_ATTEMPTS}" ]; do
    if sh /scripts/postgres-dump.sh; then
      return 0
    fi

    echo "Database backup attempt ${attempt}/${BACKUP_MAX_ATTEMPTS} failed; retrying in ${BACKUP_RETRY_SECONDS}s"
    attempt=$((attempt + 1))
    sleep "${BACKUP_RETRY_SECONDS}"
  done

  echo "Database backup failed after ${BACKUP_MAX_ATTEMPTS} attempts"
  return 1
}

while true; do
  run_backup_with_retry

  find "${BACKUP_DIR}" \
    -type f \
    -name "*.dump" \
    -mtime "+${BACKUP_RETENTION_DAYS}" \
    -delete

  sleep "${BACKUP_INTERVAL_SECONDS}"
done
