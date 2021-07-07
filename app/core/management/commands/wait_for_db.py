import logging
import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    log = logging.getLogger(__name__)

    def handle(self, *args, **kwargs):
        self.log.info("Waiting for database")
        db_connection = None
        while not db_connection:
            try:
                db_connection = connections["default"]
            except OperationalError:
                self.log.warning("Database unavailable; waiting 1 second")
                time.sleep(1)
        self.log.info("Database is available")
