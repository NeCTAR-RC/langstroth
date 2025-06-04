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

echo "** Starting Django compress **"
./manage.py compress --verbosity 3
echo "** Completed Django compress **"

gunicorn --bind :80 --access-logfile=- --worker-tmp-dir /dev/shm --forwarded-allow-ips '*' --access-logformat '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' --workers 3 langstroth.wsgi
