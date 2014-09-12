# Django settings for langstroth project.
from os import path
from os import environ

PROD_ENVIRONMENT = 0
DEV_ENVIRONMENT = 1
UAT_ENVIRONMENT = 2

# Adjust this depending on the environment.
# The install.sh script modifies this to be UAT_ENVIRONMENT.
CURRENT_ENVIRONMENT = DEV_ENVIRONMENT

TEST_MODE = 'DJANGO_TEST' in environ and environ['DJANGO_TEST'] == 'True'

# Either set these values as environment variables in the Eclipse IDE
# Or have the install_uat.sh script sed them to the real passwords.
DB_PASSWORD = environ['LANGSTROTH_DEV_DB_PASSWORD']
NAGIOS_PASSWORD = environ['LANGSTROTH_DEV_NAGIOS_PASSWORD']

DEFAULT_DATABASE_NAME = 'langstroth'
ALLOCATION_DATABASE_NAME = 'allocations'
if CURRENT_ENVIRONMENT == DEV_ENVIRONMENT:
    DEFAULT_DATABASE_NAME = 'langstroth'
    ALLOCATION_DATABASE_NAME = 'nectar_allocations'
    
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

if TEST_MODE:
    DATABASES = {
        # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
        'default': {
                'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
                'NAME': path.join(path.dirname(__file__), DEFAULT_DATABASE_NAME),                      # Or path to database file if using sqlite3.
                'TEST_NAME': path.join(path.dirname(__file__), DEFAULT_DATABASE_NAME),
            },
        # See: https://docs.djangoproject.com/en/1.6/topics/db/multi-db/
        'allocations_db': {
                'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
                'NAME': path.join(path.dirname(__file__), ALLOCATION_DATABASE_NAME),                      # Or path to database file if using sqlite3.
                'TEST_NAME': path.join(path.dirname(__file__), ALLOCATION_DATABASE_NAME),
        }
    }   
    DATABASE_ROUTERS = ['nectar_allocations.router_for_testing.TestRouter']   
else:
    DATABASES = {
         # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': DEFAULT_DATABASE_NAME,                      # Or path to database file if using sqlite3.
            # The following settings are not used with sqlite3:
            'USER': 'langstroth_user', # over-rides what is in my.cnf [client]
            'PASSWORD': DB_PASSWORD, # over-rides what is in my.cnf [client]
            'HOST': '',             # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
            'PORT': '',                      # Set to empty string for default.
            'OPTIONS': {
                'read_default_file': '/private/etc/my.cnf',
                'init_command': 'SET storage_engine=INNODB',    # Disable after the tables are created.
            },
        },
         # See: https://docs.djangoproject.com/en/1.6/topics/db/multi-db/
        'allocations_db': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': ALLOCATION_DATABASE_NAME,                      # Or path to database file if using sqlite3.
            # The following settings are not used with sqlite3:
            'USER': 'langstroth_user', # over-rides what is in my.cnf [client]
            'PASSWORD': DB_PASSWORD, # over-rides what is in my.cnf [client]
            'HOST': '',             # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
            'PORT': '',                      # Set to empty string for default.
            'OPTIONS': {
                'read_default_file': '/private/etc/my.cnf',
                'init_command': 'SET storage_engine=INNODB',    # Disable after the tables are created.
            },
        }
    }   
    DATABASE_ROUTERS = ['nectar_allocations.router.AllocationsRouter']

# Password strings populated by an edited version of the install_uat.sh script.
if CURRENT_ENVIRONMENT == DEV_ENVIRONMENT:
    NAGIOS_URL = "http://localhost:8000/static/avail.html"
    NAGIOS_AUTH = ("user", "password")
    GRAPHITE_URL = "http://graphite.dev.rc.nectar.org.au"
    NAGIOS_AVAILABILITY_URL = NAGIOS_URL
    NAGIOS_STATUS_URL = "http://localhost:8000/static/status.html"
elif CURRENT_ENVIRONMENT == UAT_ENVIRONMENT:
    NAGIOS_URL = "http://langstroth.doesntexist.com/static/avail.html"
    NAGIOS_AUTH = ("nectar", NAGIOS_PASSWORD)    # set password via sudo htpasswd /usr/local/nectar/.htpasswd nectar
    GRAPHITE_URL = "http://graphite.dev.rc.nectar.org.au"
    NAGIOS_AVAILABILITY_URL = NAGIOS_URL
    NAGIOS_STATUS_URL = "http://langstroth.doesntexist.com/static/status.html"
elif CURRENT_ENVIRONMENT == PROD_ENVIRONMENT:
    NAGIOS_URL = "http://nagios.test/cgi-bin/nagios3/" # Dummy service. Replace in production.
    NAGIOS_AUTH = ("sam", NAGIOS_PASSWORD) # Dummy password. Replace in production.
    GRAPHITE_URL = "http://graphite.mgmt.melbourne.rc.nectar.org.au" # Dummy service. Replace in production.

NAGIOS_SERVICE_GROUP = 'f5-endpoints'


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
    path.join(path.dirname(__file__), "static"),
    path.join(path.dirname(__file__), "data"),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
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

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'langstroth.wsgi.application'

TEMPLATE_DIRS = (
    path.join(path.dirname(__file__), "templates"),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
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

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

print path.join(path.dirname(__file__), "../logs/debug.log")
                
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
