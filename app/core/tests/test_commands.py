import logging

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase
from unittest.mock import patch


class CommandTests(TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_wait_for_db_ready(self):
        """Test on waiting until db is available, while available"""
        with patch("django.db.utils.ConnectionHandler.__getitem__") as gi:
            gi.return_value = True
            call_command("wait_for_db")
            self.assertEqual(gi.call_count, 1)

    @patch("time.sleep", return_value=True)
    def test_wait_for_db(self, _):
        """Test on waiting until db is available"""
        with patch("django.db.utils.ConnectionHandler.__getitem__") as gi:
            # Throw an OperationalError 5 times, then return True
            gi.side_effect = [
                OperationalError,
                OperationalError,
                OperationalError,
                OperationalError,
                OperationalError,
                True,
            ]
            call_command("wait_for_db")
            self.assertEqual(gi.call_count, 6)

    def tearDown(self):
        logging.disable(logging.NOTSET)
