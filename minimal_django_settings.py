"""
Minimal Django settings for generating migrations.
"""
import os
import sys

# Add the forms package to Python path
sys.path.insert(0, '/home/nexgensis/Documents/QMS/revamp_2.1/packages/django-nexgensis-forms')

SECRET_KEY = 'temporary-key-for-migrations'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'nexgensis_forms',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
