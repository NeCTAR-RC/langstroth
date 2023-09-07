#!/bin/bash -e

if [ -f /vault/secrets/settings ]; then
    echo "** Loading secrets from /vault/secrets/settings **"
    . /vault/secrets/settings
else
    echo "** Secrets not found! **"
fi

if [ "${DJANGO_MIGRATE:-no}" == "yes" ]; then
  echo "** Starting Django migrate **"
  ./manage.py migrate
else
  echo "** Skipping Django migrate **"
fi

echo "** Starting Django collectstatic **"
./manage.py collectstatic --noinput
echo "** Completed Django collectstatic **"

gunicorn --bind :80 --access-logfile=- --worker-tmp-dir /dev/shm --workers 3 langstroth.wsgi
