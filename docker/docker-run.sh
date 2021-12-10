#!/bin/bash -e

if [ "$DJANGO_MIGRATE:-no" == "yes" ]; then
  echo "** Starting Django migrate **"
  ./manage.py migrate
else
  echo "** Skipping Django migrate **"
fi

echo "** Starting Django collectstatic **"
./manage.py collectstatic --noinput
echo "** Completed Django collectstatic **"

gunicorn --log-file=- --bind :80 --workers 3 langstroth.wsgi
