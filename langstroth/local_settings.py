# -*- mode: python -*-

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Sam Morrison', 'sam.morrison@unimelb.edu.au'),
)

SERVER_EMAIL = 'root@status.rc.nectar.org.au'
MANAGERS = ADMINS

# Required for Django 1.5.
# If langstroth is running in production (DEBUG is False), set this
# with the list of host/domain names that the application can serve.
# For more information see:
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

DATABASES = {
    # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'langstroth',
        'USER': 'langstroth',
        'PASSWORD': 'Die9dah_Z@emoos',
        'HOST': 'db1',
        'PORT': '3306'},
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': ['status:11211']
    }
}


# The URL to your Nagios installation.
NAGIOS_URL = "http://mon.melbourne.nectar.org.au/cgi-bin/nagios3/"

# The user and password to authenticate to Nagios as.
NAGIOS_AUTH = ("sam", "nectar")

# The service group to use for calculating if services are up and
# their availability.
NAGIOS_SERVICE_GROUP = 'f5-endpoints'

# The URL to the graphite web interface
GRAPHITE_URL = "http://graphite.mgmt.rc.nectar.org.au"

# URL of allocation api
ALLOCATION_API_URL = "https://allocations.rc.nectar.org.au/rest_api"

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
MEDIA_ROOT = '/var/lib/langstroth/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/var/lib/langstroth/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

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
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': '/var/log/langstroth/debug.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    }
}
