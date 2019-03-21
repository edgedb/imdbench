#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ca9s@!n%62$4bhgboeod#vk%2kl@56=m%s%&)zwis!i2(-qq)^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('BENCH_DEBUG', '').lower() == 'true'

ALLOWED_HOSTS = ['localhost']

# Application definition

INSTALLED_APPS = [
    '_django.apps.WebappConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
]

CONN_MAX_AGE = None

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_bench',
        'USER': 'django_bench',
        'PASSWORD': 'edgedbbenchmark',
        'HOST': 'localhost',
        'PORT': '',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': os.getenv('BENCH_NOLOG', '').lower() == 'true',
}
