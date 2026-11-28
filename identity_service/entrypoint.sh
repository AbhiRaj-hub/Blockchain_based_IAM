#!/bin/sh
# Container entrypoint. `web` (default) migrates then serves; anything else is exec'd as given.
set -e
if [ -z "$1" ] || [ "$1" = "web" ]; then
  python manage.py migrate --noinput
  python manage.py createcachetable
  python manage.py collectstatic --noinput > /dev/null
  if [ -n "$ADMIN_PASSWORD" ]; then
    python manage.py create_admin --noinput --if-none-exists || echo "WARNING: could not bootstrap admin"
  fi
  exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 \
       --workers "${GUNICORN_WORKERS:-2}" --access-logfile - --forwarded-allow-ips="*"
fi
exec "$@"
