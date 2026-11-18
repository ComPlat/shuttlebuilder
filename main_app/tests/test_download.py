import logging
import os
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from main_app.build import BuildError
from main_app.models import ShuttleInstance

PASSWORD = "dummy-Secret-pw"


class ShuttleDownloadTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("owner", password="x")
        cls.other = User.objects.create_user("other", password="x")
        cls.staff = User.objects.create_user("staff", password="x", is_staff=True)
        with tempfile.TemporaryDirectory() as tmp:
            old = os.getcwd()
            os.chdir(tmp)
            try:
                cls.inst = ShuttleInstance.objects.create(
                    name="dl-test", user="dummy-user", password=PASSWORD, transfer="webdav", src="/s", dst="/d",
                    shuttle_type="file", owner=cls.owner)
            finally:
                os.chdir(old)
        cls.url = reverse("scd_view_shuttle_download", kwargs={"pk": cls.inst.pk})

    def _get(self, user):
        self.client.force_login(user)
        return self.client.get(self.url)

    def _assert_clean(self, resp):
        text = resp.content.decode()
        self.assertNotIn(PASSWORD, text)
        self.assertNotIn("dummy-user", text)
        self.assertNotIn("compilation error", text)
        self.assertNotIn("instead of", text)

    def _err(self):
        return BuildError("Building the Shuttle failed.", detail="step <go build> failed: x&y", reference="abc12345")

    def test_staff_sees_detail_and_reference(self):
        with mock.patch("main_app.models.ShuttleInstance.build", side_effect=self._err()):
            resp = self._get(self.staff)
        self.assertEqual(resp.status_code, 500)
        text = resp.content.decode()
        self.assertIn("Building the Shuttle failed.", text)
        self.assertIn("abc12345", text)
        self.assertIn("<pre>step &lt;go build&gt; failed: x&amp;y</pre>", text)
        self._assert_clean(resp)

    def test_owner_sees_message_and_reference_only(self):
        with mock.patch("main_app.models.ShuttleInstance.build", side_effect=self._err()):
            resp = self._get(self.owner)
        self.assertEqual(resp.status_code, 500)
        text = resp.content.decode()
        self.assertIn("Building the Shuttle failed.", text)
        self.assertIn("abc12345", text)
        self.assertNotIn("go build", text)
        self.assertNotIn("<pre>", text)
        self._assert_clean(resp)

    def test_generic_exception_is_logged_and_hidden(self):
        with mock.patch("main_app.models.ShuttleInstance.build", side_effect=RuntimeError("boom " + PASSWORD)):
            with self.assertLogs("main_app.build", level=logging.ERROR) as cm:
                resp = self._get(self.staff)
        self.assertEqual(resp.status_code, 500)
        text = resp.content.decode()
        self.assertIn("Building the Shuttle failed.", text)
        self.assertNotIn("<pre>", text)
        self.assertNotIn("boom", text)
        self._assert_clean(resp)
        self.assertTrue(any("dl-test" in r.getMessage() for r in cm.records))
        self.assertTrue(any(r.exc_info for r in cm.records))
        self.assertNotIn("dummy-user", "\n".join(r.getMessage() for r in cm.records))

    def test_ioerror_is_404_and_build_error_is_not_swallowed(self):
        with mock.patch("main_app.models.ShuttleInstance.build", side_effect=FileNotFoundError("x")):
            resp = self._get(self.owner)
        self.assertEqual(resp.status_code, 404)

    def test_foreign_instance_is_404(self):
        with mock.patch("main_app.models.ShuttleInstance.build") as b:
            resp = self._get(self.other)
        self.assertEqual(resp.status_code, 404)
        b.assert_not_called()

    def test_missing_instance_is_404(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse("scd_view_shuttle_download", kwargs={"pk": 99999}))
        self.assertEqual(resp.status_code, 404)

    def test_success_downloads_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "shuttle")
            with open(exe, "wb") as f:
                f.write(b"BIN")
            with mock.patch("main_app.models.ShuttleInstance.build", return_value=exe), \
                    mock.patch("main_app.models.ShuttleInstance.only_exe", return_value=True):
                resp = self._get(self.owner)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"BIN")
