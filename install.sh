#!/bin/bash

# Install the Langstroth web application on the demo server.
# The demo server publishes Langstroth using Apache2 and the WSGI module.

# Configure the langstroth.conf file to publish static content.
# See: https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/modwsgi/#serving-files
#sudo vi /etc/apache2/sites-available/langstroth.conf
#sudo service apache2 restart

git archive --format=tar --prefix=langstroth/ --remote=git@code.vpac.org:ncr002-dataanalysis/ncr002-langstroth.git  master | tar -xf -

TODAY=`date +"%Y%m%d"`
sudo mv /usr/local/django/langstroth /usr/local/django/langstroth-$TODAY
sudo mv ~/langstroth /usr/local/django

sudo mkdir -p /usr/local/django/langstroth/apache/logs

sudo mkdir -p /usr/local/django/langstroth/static

sudo cp -R /usr/local/django/langstroth/langstroth/static/* /usr/local/django/langstroth/static
sudo cp -R /usr/local/django/langstroth/langstroth/data/* /usr/local/django/langstroth/static

#cd /usr/local/django/langstroth/langstroth/static/js
#sudo vi allocations_pie.js
