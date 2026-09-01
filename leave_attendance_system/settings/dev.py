from .base import *

DEBUG = True

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default='postgresql://postgres:password@localhost:5432/leave_attendance_db'
    )
}
