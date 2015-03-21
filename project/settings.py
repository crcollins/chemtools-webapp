import os
import random
import hashlib

from Crypto.Cipher import AES
from Crypto import Random


ROOT_PATH = os.getcwd()

try:
    from secret_key import SECRET_KEY, AES_KEY
except ImportError:
    path = os.path.join(ROOT_PATH, "project/secret_key.py")
    letters = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    key = ''.join([random.choice(letters) for i in xrange(64)])
    aes_key = Random.new().read(AES.block_size)
    with open(path, "w") as f:
        f.write("SECRET_KEY = '%s'\n" % key)
        f.write("AES_KEY = b" + repr(aes_key) + '\n')
    from secret_key import SECRET_KEY, AES_KEY

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SSL = os.environ.get('HTTPS')

if SSL:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
    os.environ['wsgi.scheme'] = 'https'
    os.environ['HTTPS'] = 'on'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(ROOT_PATH, 'database'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

AUTH_USER_MODEL = 'account.CustomUser'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

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
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(ROOT_PATH, "project", "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/chem/"
LOGOUT_URL = "/logout/"
HOME_URL = "/chem/"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(ROOT_PATH, "project/static/"),
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

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
    #     'django.template.loaders.eggs.Loader',
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

ROOT_URLCONF = 'project.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'project.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, "project/templates"),
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "chemtools.context_processors.default_keywords",
    "cluster.context_processors.running_jobs",
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'chem',
    'chemtools',
    'account',
    'docs',
    'data',
    'cluster',
    'crispy_forms',
)

try:
    import sslserver
    INSTALLED_APPS = INSTALLED_APPS + ('sslserver', )
except ImportError:
    pass

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
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
       'logfile': {
            'level':'WARNING',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "logfile.log",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console':{
            'level':'WARNING',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {
            'handlers': ['logfile'],#'console'],
            'level': 'WARNING',
            'propagate': True,
        },
    }
}