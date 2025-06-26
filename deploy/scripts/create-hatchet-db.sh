#!/bin/bash

set -e
echo 'Waiting for PostgreSQL to be ready...'
while ! pg_isready -h hatchet-postgres -p 5432 -U ${HATCHET_POSTGRES_USER}; do
  sleep 1
done

echo 'PostgreSQL is ready, checking if database exists...'
if ! PGPASSWORD=${HATCHET_POSTGRES_PASSWORD} psql -h hatchet-postgres -p 5432 -U ${HATCHET_POSTGRES_USER} -lqt | grep -qw ${HATCHET_POSTGRES_DBNAME}; then
  echo 'Database does not exist, creating it...'
  PGPASSWORD=${HATCHET_POSTGRES_PASSWORD} createdb -h hatchet-postgres -p 5432 -U ${HATCHET_POSTGRES_USER} -w ${HATCHET_POSTGRES_DBNAME}
else
  echo 'Database already exists, skipping creation.'
fi
