"""Free Render web service with an external persistent PostgreSQL database."""
import os

from .render_settings import *  # noqa: F403
from .postgres import postgres_database

DATABASES = {'default': postgres_database(os.environ.get('DATABASE_URL', ''))}
