# Django settings for langstroth project.
from os import path
import sys
from urllib.parse import urlsplit

# Define this in the actual setting file
# AND in the domain field of the sites database table.
# It's used by a consistency check to ensure that siteemap.xml
# has the correct domain for all its page URL entries.
SITE_DOMAIN = ""

DEFAULT_DATABASE_NAME = '../langstroth.db'

NAGIOS_PASSWORD = ""

# Safe default for production. Developer setups and the test settings
# (settings_test.py / settings_selenium.py) flip this on explicitly.
DEBUG = False

COMPRESS_ENABLED = not DEBUG
COMPRESS_OFFLINE = not DEBUG

# If USE_OIDC is True we will use OIDC for authentication for the
# Admin site.  If False, use classic username + password.
USE_OIDC = False

# OpenID Connect Auth settings.
#
# When USE_OIDC=True, the override file (/etc/langstroth/settings.py)
# must supply OIDC_RP_CLIENT_ID and OIDC_RP_CLIENT_SECRET, and override
# OIDC_SERVER_URL (which the endpoints below derive from). See
# settings_example.py.

OIDC_SERVER_URL = 'dummy-id'

# OIDC_RP_CLIENT_ID = '<set in /etc/langstroth/settings.py>'
# OIDC_RP_CLIENT_SECRET = '<set in /etc/langstroth/settings.py>'

OIDC_RP_SIGN_ALGO = 'RS256'

# OIDC_RP_SCOPES should include a scope that serves the ``roles`` claim
# in the ID token, with an array of user's roles.
OIDC_RP_SCOPES = 'openid email'

# OpenID Connect endpoints (derived from OIDC_SERVER_URL).
OIDC_OP_AUTHORIZATION_ENDPOINT = f'{OIDC_SERVER_URL}/auth'
OIDC_OP_TOKEN_ENDPOINT = f'{OIDC_SERVER_URL}/token'
OIDC_OP_USER_ENDPOINT = f'{OIDC_SERVER_URL}/userinfo'
OIDC_OP_JWKS_ENDPOINT = f'{OIDC_SERVER_URL}/certs'

OIDC_USERNAME_ALGO = 'langstroth.auth.generate_username'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


def path_merge(pathname, filename):
    """Returns the absolute path to the merged dirname of the pathname and
    filename.
    """
    return path.abspath(path.join(path.dirname(pathname), filename))


DATABASES = {
    # See: https://docs.djangoproject.com/en/1.6/intro/tutorial01/
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path_merge(__file__, DEFAULT_DATABASE_NAME),
        'TEST_NAME': path_merge(__file__, DEFAULT_DATABASE_NAME),
    },
}

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# The URL to your Nagios installation.
NAGIOS_URL = "http://nagios.test/cgi-bin/nagios3/"

# The user and password to authenticate to Nagios as.
NAGIOS_AUTH = ("", "")

# The service group to use for calculating if services are up and
# their availability.
NAGIOS_SERVICE_GROUP = 'f5-endpoints'

AVAILABILITY_QUERY_TEMPLATE = (
    "avail.cgi"
    "?t1=%s"
    "&t2=%s"
    "&show_log_entries="
    "&servicegroup=%s"
    "&assumeinitialstates=yes"
    "&assumestateretention=yes"
    "&assumestatesduringnotrunning=yes"
    "&includesoftstates=yes"
    "&initialassumedhoststate=3"
    "&initialassumedservicestate=6"
    "&timeperiod=[+Current+time+range+]"
    "&backtrack=4"
)
STATUS_QUERY_TEMPLATE = "status.cgi?servicegroup=%s&style=detail"

# The URL to the graphite web interface
GRAPHITE_URL = "http://graphite.test"

ALLOCATION_API_URL = "http://allocations.test/rest_api/"

# This determines which FoR code series will be requested from the
# allocations API.  Values understood by the server are "2008", "2020"
# and "all".  The "all" option means all FoR codes subject to server-side
# filtering.
FOR_CODE_SERIES = "all"

# This lists the 2-digit code ranges for each FoR code series.  For example,
# ANZSRC 2008 defines 2-digit FoR codes "01" through "22" inclusive.
FOR_CODE_RANGES = {
    "2008": ("01", "22"),
    "2020": ("30", "52"),
    "all": ("00", "99"),
}

# Date from which graphite user statistics began to be collected.
USER_STATISTICS_START_DATE = '20111201'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-au'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# These countries will be prioritized in the search
# for a matching timezone. Consider putting your
# app's most popular countries first.
# Defaults to the top Internet using countries.
TZ_DETECT_COUNTRIES = ('AU', 'NZ')

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
STATIC_ROOT = 'static'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
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
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (('text/x-scss', 'django_libsass.SassCompiler'),)

# Cookie / transport security. These defaults are safe in production
# (DEBUG=False) and are auto-relaxed for local dev (DEBUG=True) so a
# developer running over plain HTTP can still log in.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = not DEBUG
# Trust X-Forwarded-Proto from the front proxy. Only safe because the
# deployment terminates TLS at a known proxy that strips this header
# from external traffic; if you change deployment topology, revisit
# along with gunicorn's --forwarded-allow-ips.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'langstroth.auth.NoDjangoAdminForEndUserMiddleware',
    'tz_detect.middleware.TimezoneMiddleware',
]

# Content Security Policy. The site has inline scripts in several
# templates (allocation_visualisation.html, index.html starfield,
# create.html tz-offset, footer.html mailchimp + date.getFullYear,
# etc.) and bootstrap-datepicker injects inline styles, so we allow
# 'unsafe-inline' here. Tighten further by extracting inline blocks
# into static files and adopting nonces.
#
# bootstrap_datepicker_plus's default widget media references
# moment.js, eonasdan-bootstrap-datetimepicker, bootstrap-icons and
# its own widget JS/CSS from cdn.jsdelivr.net, and bootstrap-icons
# loads its webfont from the same host -- so jsdelivr is allowed in
# script-/style-/font-src. Vendoring those assets locally would let
# us drop the CDN allowance.
#
# static/scss/main.scss @imports the Figtree family from Google
# Fonts: that stylesheet is fetched from fonts.googleapis.com and
# the .woff2 files it references come from fonts.gstatic.com, so
# both hosts are allowed.
#
# /allocations/ fetches data straight from ALLOCATION_API_URL in
# the browser (see static/js/allocations_pie.js, project_details.js),
# so its origin needs to be in connect-src. settings.py re-runs
# _build_csp() after the override file has had a chance to change
# ALLOCATION_API_URL -- otherwise prod would only allow the
# placeholder value baked into defaults.
CDN_JSDELIVR = 'https://cdn.jsdelivr.net'
GOOGLE_FONTS_CSS = 'https://fonts.googleapis.com'
GOOGLE_FONTS_FILES = 'https://fonts.gstatic.com'


def _origin(url):
    """Return ``scheme://host[:port]`` for a URL, or None if it has none."""
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"


def build_csp(allocation_api_url):
    connect_src = ["'self'"]
    allocation_origin = _origin(allocation_api_url)
    if allocation_origin and allocation_origin not in connect_src:
        connect_src.append(allocation_origin)
    return {
        'DIRECTIVES': {
            'default-src': ("'self'",),
            'script-src': ("'self'", "'unsafe-inline'", CDN_JSDELIVR),
            'style-src': (
                "'self'",
                "'unsafe-inline'",
                CDN_JSDELIVR,
                GOOGLE_FONTS_CSS,
            ),
            'img-src': ("'self'", 'data:', 'https:'),
            'font-src': (
                "'self'",
                'data:',
                CDN_JSDELIVR,
                GOOGLE_FONTS_FILES,
            ),
            'connect-src': tuple(connect_src),
            'frame-ancestors': ("'none'",),
            'base-uri': ("'self'",),
            'form-action': ("'self'",),
            'object-src': ("'none'",),
        },
    }


CONTENT_SECURITY_POLICY = build_csp(ALLOCATION_API_URL)

ROOT_URLCONF = 'langstroth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS = [
    'langstroth',
    'langstroth.outages',
    'langstroth.nectar_allocations',
    'langstroth.user_statistics',
    'django.contrib.admin',
    'django.contrib.auth',
    'mozilla_django_oidc',
    'django.contrib.humanize',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'bootstrap_datepicker_plus',
    'django_filters',
    'compressor',
    'tz_detect',
    'health_check',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'langstroth.auth.NectarAuthBackend',
]

AUTH_USER_MODEL = 'langstroth.User'

LOGIN_REDIRECT_URL = "/"

LOGIN_URL = "/admin/login"

WSGI_APPLICATION = 'langstroth.wsgi.application'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

REST_FRAMEWORK = {'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%S%z"}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '%(levelname)s %(message)s'},
    },
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
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
    },
}
