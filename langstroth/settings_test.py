# Django test settings for langstroth project.
from os import path

# Pick up the default settings then override them in this file.
from .defaults import *  # NOQA

TEST_MODE = True

DEFAULT_DATABASE_NAME = '../langstroth.db'
ALLOCATION_DATABASE_NAME = '../nectar_allocations.db'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': path.join(path.dirname(__file__),
                          DEFAULT_DATABASE_NAME),
        'TEST_NAME': path.join(path.dirname(__file__),
                               DEFAULT_DATABASE_NAME),
        },
    # See: https://docs.djangoproject.com/en/1.6/topics/db/multi-db/
    'allocations_db': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': path.join(path.dirname(__file__),
                          ALLOCATION_DATABASE_NAME),
        'TEST_NAME': path.join(path.dirname(__file__),
                               ALLOCATION_DATABASE_NAME),
    }
}
DATABASE_ROUTERS = ['nectar_allocations.router_for_testing.TestRouter']
FIXTURE_DIRS = ()

# Password strings populated by an edited version of the install_uat.sh script.
NAGIOS_URL = "http://localhost:8000/static/avail.html"
NAGIOS_AUTH = ("user", "password")
AVAILABILITY_QUERY_TEMPLATE = ""
STATUS_QUERY_TEMPLATE = ""
NAGIOS_STATUS_URL = "http://localhost:8000/static/status.html"

GRAPHITE_URL = "http://graphite.dev.rc.nectar.org.au"

# Additional locations of static files
STATICFILES_DIRS = (
    path.join(path.dirname(__file__), 'static'),
    path.join(path.dirname(__file__), 'data'),

    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'langstroth',
    'nectar_status',
    'nectar_allocations',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

LOGGING['handlers']['file'] = {
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    # Create the log directory with the correct permissions by hand.
    'filename':     path.join(path.dirname(__file__), "../logs/debug.log"),
}
