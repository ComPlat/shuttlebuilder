import io
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class InitSuperuserTest(TestCase):
    def run_cmd(self, **env):
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=False), mock.patch("sys.stdout", out):
            for key in ("DJANGO_SUPERUSER_USERNAME", "DJANGO_SUPERUSER_EMAIL", "DJANGO_SUPERUSER_PASSWORD"):
                if key not in env:
                    os.environ.pop(key, None)
            call_command("initsuperuser")
        return out.getvalue()

    def test_without_username_does_nothing(self):
        # the container entrypoint runs with set -e: a missing admin user must not stop the start
        out = self.run_cmd()
        self.assertIn("not set", out)
        self.assertFalse(get_user_model().objects.filter(is_superuser=True).exists())

    def test_creates_once(self):
        env = dict(DJANGO_SUPERUSER_USERNAME="admin1", DJANGO_SUPERUSER_EMAIL="a@example.org",
                   DJANGO_SUPERUSER_PASSWORD="dummy-pass-123")
        self.run_cmd(**env)
        self.assertIn("already", self.run_cmd(**env))
        self.assertEqual(get_user_model().objects.filter(username="admin1", is_superuser=True).count(), 1)
