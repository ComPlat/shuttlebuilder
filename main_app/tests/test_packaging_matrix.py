"""Packaging matrix: every architecture x transfer x converter x certificate combination.

The build is mocked (it returns a fake executable); STATIC_ROOT and MEDIA_ROOT are temp dirs with fake files.
The expectations are written down independently of `only_exe()` / `_zip_name()` so the test checks them, too.
"""
import io
import itertools
import os
import tempfile
import zipfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from main_app.models import ShuttleInstance

ARCHITECTURES = ('win_i386', 'win_64', 'ubuntu_64', 'raspberry_pi_6', 'raspberry_pi_7', 'raspberry_pi_64')
CONVERTER_ARCHITECTURES = ('win_64', 'ubuntu_64')
TRANSFERS = ('webdav', 'sftp')
CERT = b"-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----\n"
PROFILE = b'{"dummy": true}'
WINSCP = ('license.txt', 'WinSCP.com', 'WinSCP.exe')


def combinations():
    for arch, transfer in itertools.product(ARCHITECTURES, TRANSFERS):
        for converter in ((False, True) if arch in CONVERTER_ARCHITECTURES else (False,)):
            for cert in ((False, True) if transfer == 'webdav' else (False,)):
                yield arch, transfer, converter, cert


def expected(arch, transfer, converter, cert, profile_name=''):
    """(bare exe?, zip name, sorted zip members) for one combination."""
    exe = 'shuttle.exe' if arch.startswith('win') else 'shuttle'
    xp_sftp = arch == 'win_i386' and transfer == 'sftp'
    if not (cert or xp_sftp or converter):
        return True, None, None
    if xp_sftp:
        zip_name = 'shuttle_sftp_winxp.zip'
    elif converter:
        zip_name = 'shuttle_with_converter.zip'
    else:
        zip_name = 'shuttle_%s.zip' % arch
    members = {exe, 'INSTALL.txt'}
    if xp_sftp:
        members.update(WINSCP)
    if converter:
        members.add('ChemConverterApp.exe' if arch == 'win_64' else 'ChemConverterApp')
        members.add(profile_name)  # the stored name, e.g. profiles/profile_AbC.json
    if cert:
        members.add('server.crt')
    return False, zip_name, sorted(members)


class PackagingMatrixTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('matrix-owner', password='x')

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = tmp.name
        self.media = os.path.join(root, 'media')
        self.static = os.path.join(root, 'static')
        self.bin = os.path.join(root, 'bin')
        os.makedirs(os.path.join(self.static, 'files'))
        os.makedirs(self.bin)
        for name in WINSCP + ('ChemConverterApp', 'ChemConverterApp.exe'):
            with open(os.path.join(self.static, 'files', name), 'wb') as f:
                f.write(b'fake ' + name.encode())
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(root)  # ./projects/builds/<name> is created relative to the cwd
        ov = override_settings(MEDIA_ROOT=self.media, STATIC_ROOT=self.static)
        ov.enable()
        self.addCleanup(ov.disable)
        self.client.force_login(self.owner)

    def _instance(self, index, arch, transfer, converter, cert):
        inst = ShuttleInstance(
            name='matrix-%d' % index, user='dummy-user', password='dummy-pw', transfer=transfer, src='/s',
            dst='/d', shuttle_type='file', owner=self.owner, architecture=arch, with_converter=converter,
            dst_bagit='/b' if converter else None, user_bagit='u' if converter else None,
            passwort_bagit='p' if converter else None)
        if cert:
            inst.cert.save('server.crt', SimpleUploadedFile('server.crt', CERT), save=False)
        if converter:
            inst.profile.save('profile.json', SimpleUploadedFile('profile.json', PROFILE), save=False)
        inst.save()
        return inst

    def _fake_exe(self, arch):
        path = os.path.join(self.bin, 'shuttle.exe' if arch.startswith('win') else 'shuttle')
        with open(path, 'wb') as f:
            f.write(b'BIN')
        return path

    def test_matrix_size(self):
        # 4 archs without converter: webdav (2 cert states) + sftp (1) = 3 each;
        # 2 archs with converter option: (webdav 2 + sftp 1) x 2 converter states = 6 each
        self.assertEqual(len(list(combinations())), 4 * 3 + 2 * 6)

    def test_every_combination(self):
        for index, combo in enumerate(combinations()):
            arch, transfer, converter, cert = combo
            with self.subTest(arch=arch, transfer=transfer, converter=converter, cert=cert):
                inst = self._instance(index, *combo)
                bare, zip_name, members = expected(*combo, profile_name=inst.profile.name)
                self.assertEqual(inst.only_exe(), bare)
                for leftover in os.listdir(self.bin):
                    os.remove(os.path.join(self.bin, leftover))
                exe = self._fake_exe(arch)
                url = reverse('scd_view_shuttle_download', kwargs={'pk': inst.pk})
                with mock.patch('main_app.models.ShuttleInstance.build', return_value=exe):
                    resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)
                if bare:
                    self.assertEqual(resp.content, b'BIN')
                    self.assertIn('filename="%s"' % os.path.basename(exe), resp['Content-Disposition'])
                else:
                    self.assertIn('filename="%s"' % zip_name, resp['Content-Disposition'])
                    zf = zipfile.ZipFile(io.BytesIO(resp.content))
                    self.assertEqual(sorted(zf.namelist()), members)
                    self.assertEqual(zf.read(os.path.basename(exe)), b'BIN')
                    if cert:
                        self.assertEqual(zf.read('server.crt'), CERT)
                    if converter:
                        self.assertEqual(zf.read(inst.profile.name), PROFILE)
                    # no temporary zip is left next to the executable
                    self.assertEqual(os.listdir(self.bin), [os.path.basename(exe)])
