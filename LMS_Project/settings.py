"""
Django settings for LMS_Project project.

Generated by 'django-admin startproject' using Django 4.1.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^@eeb&6o=6x!dv6hdtm+x*@xc=!#cv)ibjx6n^#((z^zet$fa3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://exskilence-suite.azurewebsites.net",
    "https://euboard.azurewebsites.net/",
]
# Application definition
MSSQL_SERVER_NAME = 'slnkshmtbsil.database.windows.net'
MSSQL_DATABASE_NAME = 'exe_test'
MSSQL_USERNAME = 'tpssa'
MSSQL_PWD = 'TPSuser@sa123'
MSSQL_DRIVER =  'ODBC Driver 18 for SQL Server'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework', 
    'djongo',
    'LMS_Mongodb_App',
    'LMS_MSSQLdb_App',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

# blob
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage' 

AZURE_ACCOUNT_NAME = 'eustoreholder'
AZURE_ACCOUNT_KEY = 'C2+T9kL7MgZbmODARQYK/HjWSxZy2o1+IqQifEhqPAxhs/ul4pPPisrWFN50yXSBWUHy5ShSPV1B+ASthIYLYw=='
AZURE_CONTAINER = 'lmsdata'

AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'

# Set the custom domain for the storage account
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'

# Set the default ACL to 'private'
AZURE_DEFAULT_ACL = 'private'
#blob
ROOT_URLCONF = 'LMS_Project.urls'

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

WSGI_APPLICATION = 'LMS_Project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES = {
#     # 'default': {
#     #     'ENGINE': 'django.db.backends.sqlite3',
#     #     'NAME': BASE_DIR / 'db.sqlite3',
#     # }
# # }
# 'default': {
#         'ENGINE': 'djongo',
#         'NAME': 'ExskilenceNEW',
#         'ENFORCE_SCHEMA': False,  
#         'CLIENT': {
#             'host': 'mongodb+srv://kecoview:FVy5fqqCtQy3KIt6@cluster0.b9wmlid.mongodb.net/',
#             'username': 'kecoview',
#             'password': 'FVy5fqqCtQy3KIt6',
#             'authMechanism': 'SCRAM-SHA-1',
#         }
#     }


DATABASES = {
    'mongodb': {
        'ENGINE': 'djongo',
        'NAME': 'LMSmongodb',
        'CLIENT': {
            'host': 'mongodb+srv://kecoview:FVy5fqqCtQy3KIt6@cluster0.b9wmlid.mongodb.net/',
            'username': 'kecoview',
            'password': 'FVy5fqqCtQy3KIt6',
            'authMechanism': 'SCRAM-SHA-1',
        }
    },
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'eussdb',
        'USER': 'euserblr',#'eudev',#
        'PASSWORD': '6han4Sy5#',#'Devlop99@#',#
        'HOST': 'slnsgdhutmtbs.database.windows.net',
       
        # 'HOST': 'Rudresh\\SQLEXPRESS',
        'PORT': '1433',
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'trustServerCertificate': 'yes',  # Add this to avoid SSL errors
        },
    }
}
# DATABASES = {
#     'mongodb': {
#         'ENGINE': 'djongo',
#         'NAME': 'LMSmongodb',
#         'CLIENT': {
#             'host': 'mongodb+srv://kecoview:FVy5fqqCtQy3KIt6@cluster0.b9wmlid.mongodb.net/',
#             'username': 'kecoview',
#             'password': 'FVy5fqqCtQy3KIt6',
#             'authMechanism': 'SCRAM-SHA-1',
#         }
#     },
#     'default': {
#         'ENGINE': 'mssql',
#         'NAME': 'LMSdb',
#         'USER': 'sa',
#         'PASSWORD': 'sql2014!',
#         'HOST': 'localhost',
#         'PORT': '1433',
#         'OPTIONS': {
#             'driver': 'ODBC Driver 17 for SQL Server',
#         },
#     }
# }




# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MIGRATION_MODULES = {
    'LMS_Mongodb_App': None,
    # 'LMS_MSSQLdb_App': None
}
