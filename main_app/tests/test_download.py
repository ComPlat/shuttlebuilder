import io
import logging
import os
import tempfile
import zipfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse

from main_app.build import BuildError
from main_app.models import GitInstance, ShuttleInstance, ShuttleInstanceSearchForm

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


class ShuttleDownloadZipTest(TestCase):
    """Zip variants of the download (certificate, converter, WinXP)."""
    CERT = b"-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----\n"

    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("zip-owner", password="x")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = self._tmp.name
        self.media = os.path.join(root, "media")
        self.static = os.path.join(root, "static")
        self.bin = os.path.join(root, "bin")
        os.makedirs(os.path.join(self.static, "files"))
        os.makedirs(self.bin)
        for name in ("license.txt", "WinSCP.com", "WinSCP.exe", "ChemConverterApp", "ChemConverterApp.exe"):
            with open(os.path.join(self.static, "files", name), "wb") as f:
                f.write(b"fake " + name.encode())
        self.exe = os.path.join(self.bin, "shuttle.exe")
        with open(self.exe, "wb") as f:
            f.write(b"BIN")
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(root)  # delete() removes ./projects/builds/<name>
        ov = override_settings(MEDIA_ROOT=self.media, STATIC_ROOT=self.static)
        ov.enable()
        self.addCleanup(ov.disable)

    def _instance(self, name, cert=True, **kw):
        values = dict(name=name, user="dummy-user", password=PASSWORD, transfer="webdav", src="/s", dst="/d",
                      shuttle_type="file", owner=self.owner, architecture="win_64")
        values.update(kw)
        inst = ShuttleInstance(**values)
        if cert:
            inst.cert.save("server.crt", SimpleUploadedFile("server.crt", self.CERT), save=False)
        inst.save()
        return inst

    def _download(self, inst, only_exe):
        self.client.force_login(self.owner)
        url = reverse("scd_view_shuttle_download", kwargs={"pk": inst.pk})
        with mock.patch("main_app.models.ShuttleInstance.build", return_value=self.exe), \
                mock.patch("main_app.models.ShuttleInstance.only_exe", return_value=only_exe):
            return self.client.get(url)

    def _zip(self, resp):
        self.assertEqual(resp.status_code, 200)
        return zipfile.ZipFile(io.BytesIO(resp.content))

    def _no_temp_zip_left(self):
        self.assertEqual(os.listdir(self.bin), ["shuttle.exe"])

    def test_plain_zip_with_cert(self):
        resp = self._download(self._instance("zip-plain"), only_exe=False)
        self.assertIn('filename="shuttle_win_64.zip"', resp["Content-Disposition"])
        zf = self._zip(resp)
        self.assertEqual(sorted(zf.namelist()), ["server.crt", "shuttle.exe"])
        self.assertEqual(zf.read("server.crt"), self.CERT)
        self.assertEqual(zf.read("shuttle.exe"), b"BIN")
        self._no_temp_zip_left()

    def test_converter_zip_contains_cert(self):
        inst = self._instance("zip-conv", with_converter=True, dst_bagit="/b", user_bagit="u", passwort_bagit="p")
        inst.profile.save("profile.json", SimpleUploadedFile("profile.json", b"{}"), save=True)
        resp = self._download(inst, only_exe=False)
        self.assertIn('filename="shuttle_with_converter.zip"', resp["Content-Disposition"])
        zf = self._zip(resp)
        names = zf.namelist()
        self.assertIn("server.crt", names)
        self.assertIn("ChemConverterApp.exe", names)
        self.assertIn("shuttle.exe", names)
        self.assertEqual(zf.read("server.crt"), self.CERT)
        self._no_temp_zip_left()

    def test_converter_zip_without_cert(self):
        inst = self._instance("zip-conv2", cert=False, with_converter=True, dst_bagit="/b", user_bagit="u",
                              passwort_bagit="p")
        inst.profile.save("profile.json", SimpleUploadedFile("profile.json", b"{}"), save=True)
        zf = self._zip(self._download(inst, only_exe=False))
        self.assertNotIn("server.crt", zf.namelist())

    def test_winxp_sftp_zip(self):
        inst = self._instance("zip-xp", cert=False, transfer="sftp", architecture="win_i386")
        resp = self._download(inst, only_exe=False)
        self.assertIn('filename="shuttle_sftp_winxp.zip"', resp["Content-Disposition"])
        zf = self._zip(resp)
        self.assertEqual(sorted(zf.namelist()), ["WinSCP.com", "WinSCP.exe", "license.txt", "shuttle.exe"])
        self._no_temp_zip_left()

    def test_cert_is_ignored_for_sftp(self):
        inst = self._instance("zip-sftp-cert", transfer="sftp", architecture="win_i386")
        zf = self._zip(self._download(inst, only_exe=False))
        self.assertNotIn("server.crt", zf.namelist())

    def test_exe_only_stays_plain(self):
        resp = self._download(self._instance("zip-exe"), only_exe=True)
        self.assertEqual(resp.content, b"BIN")


class ListTemplatesTest(TestCase):
    """The list templates show the option badges and versions."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("list-owner", password="x")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self._tmp.name)

    def _render(self, instances, template="ShuttleInstance"):
        return render_to_string("main_app/models/%s/%s_list.html" % (template, template), {
            "instances": instances, "range": [0, 10], "range_size": 10, "total_count": len(instances),
            "search_form": ShuttleInstanceSearchForm(data={}),
        })

    def _inst(self, name, **kw):
        values = dict(name=name, user="dummy-user", password=PASSWORD, transfer="webdav", src="/s", dst="/d",
                      shuttle_type="file", owner=self.owner)
        values.update(kw)
        return ShuttleInstance.objects.create(**values)

    def test_badges(self):
        insecure = self._inst("l-insecure", insecure=True)
        nokey = self._inst("l-nokey", transfer="sftp")
        keyed = self._inst("l-keyed", transfer="sftp", host_key="SHA256:" + "A" * 43)
        dav = self._inst("l-dav")
        html = self._render([insecure, nokey, keyed, dav])
        self.assertEqual(html.count("Verification disabled"), 1)
        self.assertEqual(html.count("No host key"), 1)
        self.assertLess(html.index("l-insecure"), html.index("Verification disabled"))
        self.assertLess(html.index("l-nokey"), html.index("No host key"))
        self.assertLess(html.index("No host key"), html.index("l-keyed"))

    def test_insecure_sftp_shows_only_warning_badge(self):
        html = self._render([self._inst("l-both", transfer="sftp", insecure=True)])
        self.assertIn("Verification disabled", html)
        self.assertNotIn("No host key", html)

    def test_versions(self):
        GitInstance.objects.create(name="g", url="http://example.invalid/x.git", branch="main", is_active=True,
                                   shuttle_version="1.14")
        built = self._inst("l-built", built_version="1.13")
        fresh = self._inst("l-fresh")
        html = self._render([built, fresh])
        self.assertIn("Shuttle 1.13", html)
        self.assertIn("not built yet", html)
        self.assertIn("Downloads build Shuttle 1.14", html)

    def test_instance_name_and_version_are_escaped(self):
        html = self._render([self._inst("<b>x</b>", built_version="<i>1</i>")])
        self.assertNotIn("<b>x</b>", html)
        self.assertNotIn("<i>1</i>", html)

    def test_git_list_shows_version(self):
        git = GitInstance.objects.create(name="g2", url="http://example.invalid/y.git", branch="main",
                                         shuttle_version="1.14")
        other = GitInstance.objects.create(name="g3", url="http://example.invalid/z.git", branch="main")
        html = self._render([git, other], template="GitInstance")
        self.assertIn("Shuttle version", html)
        self.assertIn("1.14", html)
