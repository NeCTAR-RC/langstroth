# Settings file to support automated testing.

# Django test settings for langstroth project.
from os import path
from os import environ

# Pick up the default settings then override them in this file.
from .defaults import *  # NOQA

TEST_MODE = True

# Set these values as environment variables in the Eclipse IDE.
# Only needed for integration testing against a real database.
# DB_PASSWORD = environ['LANGSTROTH_DEV_DB_PASSWORD']
# NAGIOS_PASSWORD = environ['LANGSTROTH_DEV_NAGIOS_PASSWORD']

DEFAULT_DATABASE_NAME = 'langstroth'
ALLOCATION_DATABASE_NAME = 'nectar_allocations'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
    'default': {
            'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': path.join(path.dirname(__file__), DEFAULT_DATABASE_NAME),  # Or path to database file if using sqlite3.
            'TEST_NAME': path.join(path.dirname(__file__), DEFAULT_DATABASE_NAME),
        },
    # See: https://docs.djangoproject.com/en/1.6/topics/db/multi-db/
    'allocations_db': {
            'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': path.join(path.dirname(__file__), ALLOCATION_DATABASE_NAME),  # Or path to database file if using sqlite3.
            'TEST_NAME': path.join(path.dirname(__file__), ALLOCATION_DATABASE_NAME),
    }
}
DATABASE_ROUTERS = ['nectar_allocations.router_for_testing.TestRouter']

# Password strings populated by an edited version of the install_uat.sh script.
NAGIOS_AUTH = ("user", "password")
AVAILABILITY_QUERY_TEMPLATE = ""
STATUS_QUERY_TEMPLATE = ""
NAGIOS_AVAILABILITY_URL = "http://localhost:8000/static/avail.html"
NAGIOS_STATUS_URL = "http://localhost:8000/static/status.html"

GRAPHITE_URL = "http://graphite.dev.rc.nectar.org.au"

# Additional locations of static files
STATICFILES_DIRS = (
    path.join(path.dirname(__file__), "static"),
    path.join(path.dirname(__file__), "data"),

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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': path.join(path.dirname(__file__), "../logs/debug.log"),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'custom.debug': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
