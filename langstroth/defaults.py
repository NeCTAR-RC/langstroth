# Django settings for langstroth project.
import sys
from os import path

from user_statistics.settings import *  # NOQA

# Override this to TEST_MODE = False for the production settings file.
# It's True here so we can populate the database with reference data.
TEST_MODE = True

DEFAULT_DATABASE_NAME = '../langstroth.db'
ALLOCATION_DATABASE_NAME = '../nectar_allocations.db'

NAGIOS_PASSWORD = ""

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


def path_merge(pathname, filename):
    """Returns the absolute path to the merged dirname of the pathname and
    filename."""
    return path.abspath(path.join(path.dirname(pathname), filename))

DATABASES = {
    # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path_merge(__file__, DEFAULT_DATABASE_NAME),
        'TEST_NAME': path_merge(__file__, DEFAULT_DATABASE_NAME),
    },
    # See: https://docs.djangoproject.com/en/1.6/topics/db/multi-db/
    'allocations_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path_merge(__file__, ALLOCATION_DATABASE_NAME),
        'TEST_NAME': path_merge(__file__, ALLOCATION_DATABASE_NAME),
    }
}
DATABASE_ROUTERS = ['nectar_allocations.router.AllocationsRouter']
FIXTURE_DIRS = (
    path_merge(__file__, '../nectar_allocations/reference_data/')
)

# The URL to your Nagios installation.
NAGIOS_URL = "http://nagios.test/cgi-bin/nagios3/"

# The user and password to authenticate to Nagios as.
NAGIOS_AUTH = ("", "")

# The service group to use for calculating if services are up and
# their availability.
NAGIOS_SERVICE_GROUP = 'f5-endpoints'

AVAILABILITY_QUERY_TEMPLATE = "avail.cgi" \
    "?t1=%s" \
    "&t2=%s" \
    "&show_log_entries=" \
    "&servicegroup=%s" \
    "&assumeinitialstates=yes" \
    "&assumestateretention=yes" \
    "&assumestatesduringnotrunning=yes" \
    "&includesoftstates=yes" \
    "&initialassumedhoststate=3" \
    "&initialassumedservicestate=6" \
    "&timeperiod=[+Current+time+range+]" \
    "&backtrack=4"
STATUS_QUERY_TEMPLATE = "status.cgi" \
    "?servicegroup=%s" \
    "&style=detail"

# The URL to the graphite web interface
GRAPHITE_URL = "http://graphite.test"

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Australia/Melbourne'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    path_merge(__file__, "static"),
    # Put strings here, like "/home/html/static"
    # or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ofok2r^p3*m8cocztx&y7n@48(lbwij*najjyoxzxrflx@#qeh'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'langstroth.urls'

TEMPLATE_DIRS = (
    path_merge(__file__, "templates"),
    # Put strings here, like "/home/html/django_templates"
    # or "C:/www/django/templates".
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
    'user_statistics',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': sys.stderr,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {
            'handlers': ['console'],
            'level': 'WARN',
        },
    }
}
