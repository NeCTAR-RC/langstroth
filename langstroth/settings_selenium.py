# Django settings for Langstroth project's selenium tests

# Pick up the default settings then override them in this file.
from .defaults import *  # NOQA
import os
from os import path

DEBUG = True

SECRET_KEY = 'secret'

# mozilla_django_oidc reads these at backend init even when USE_OIDC=False,
# so they need to be set for tests that instantiate NectarAuthBackend.
OIDC_RP_CLIENT_ID = 'test'
OIDC_RP_CLIENT_SECRET = 'test'

# Relax production-only transport-security defaults so selenium drives
# the dev server over plain HTTP.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

COMPRESS_ENABLED = False

COMPRESS_PRECOMPILERS = []

# Password strings populated by an edited version of the install_uat.sh script.
NAGIOS_URL = "http://localhost:8000/static/avail.html"
NAGIOS_AUTH = ("user", "password")
AVAILABILITY_QUERY_TEMPLATE = ""
STATUS_QUERY_TEMPLATE = ""

GRAPHITE_URL = "http://graphite.dev.rc.nectar.org.au"

DEBUG_LOG = path_merge(__file__, "../logs/debug.log")  # NOQA

if not path.exists(path.dirname(DEBUG_LOG)):
    os.mkdir(path.dirname(DEBUG_LOG))

LOGGING['handlers']['file'] = {  # NOQA
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    # Create the log directory with the correct permissions by hand.
    'filename': DEBUG_LOG,
}

ALLOWED_HOSTS += ['testserver']  # NOQA

WHITENOISE_AUTOREFRESH = False
