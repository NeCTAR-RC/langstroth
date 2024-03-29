# Django settings for Langstroth project's unit tests

# Pick up the default settings then override them in this file.
from .defaults import *  # NOQA
import os
from os import path


DEFAULT_DATABASE_NAME = '../langstroth.db'

DEBUG = True

DATABASES = {
    # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.sqlite3',
        # Or path to database file if using sqlite3.
        'NAME': path_merge(__file__, DEFAULT_DATABASE_NAME), # NOQA
        'TEST_NAME': path_merge(__file__, DEFAULT_DATABASE_NAME), # NOQA
    },
}

# Password strings populated by an edited version of the install_uat.sh script.
NAGIOS_URL = "http://localhost:8000/static/avail.html"
NAGIOS_AUTH = ("user", "password")
AVAILABILITY_QUERY_TEMPLATE = ""
STATUS_QUERY_TEMPLATE = ""
NAGIOS_STATUS_URL = "http://localhost:8000/static/status.html"

GRAPHITE_URL = "http://graphite.dev.rc.nectar.org.au"

DEBUG_LOG = path_merge(__file__, "../logs/debug.log") # NOQA

if not path.exists(path.dirname(DEBUG_LOG)):
    os.mkdir(path.dirname(DEBUG_LOG))

LOGGING['handlers']['file'] = {  # NOQA
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    # Create the log directory with the correct permissions by hand.
    'filename': DEBUG_LOG,
}

WHITENOISE_AUTOREFRESH = False
