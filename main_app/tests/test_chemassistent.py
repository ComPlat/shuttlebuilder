"""ChemAssistent transfer type (M7): destination, API key, form rules, build config, packaging flag."""
import json

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from main_app.forms import ShuttleInstanceForm
from main_app.models import ShuttleInstance
from main_app.tests.test_options import make_pem
from main_app.validators import validate_api_key, validate_destination

KEY = 'cam_' + 'x' * 32  # dummy key


class DestinationTest(SimpleTestCase):
    def test_valid(self):
        for v in ('https://cam.example', 'https://cam.example/', 'http://cam.example:8080',
                  'https://cam.example/api/jobs/trigger', 'https://cam.example/custom/trigger/'):
            with self.subTest(v=v):
                validate_destination(v, 'chemassistent')

    def test_invalid(self):
        for v in ('ftp://cam.example', 'cam.example', 'https://', 'https:///api', 'https://cam.example:0',
                  'ssh://cam.example', ''):
            with self.subTest(v=v):
                with self.assertRaises(ValidationError):
                    validate_destination(v, 'chemassistent')


class ApiKeyTest(SimpleTestCase):
    def test_valid(self):
        validate_api_key('cam_' + 'a' * 16)  # 20 chars
        validate_api_key('cam_' + 'a' * 196)  # 200 chars
        validate_api_key(KEY)

    def test_invalid(self):
        for v in ('', 'x' * 40, 'CAM_' + 'a' * 30, 'cam_' + 'a' * 15, 'cam_' + 'a' * 197,
                  'cam_' + 'a' * 10 + ' ' + 'a' * 10, 'cam_' + 'a' * 20 + '\n', 'cam_' + 'a' * 10 + '\t' + 'a' * 10,
                  'cam_' + 'a' * 10 + '\x00' + 'a' * 10, ' cam_' + 'a' * 30):
            with self.subTest(v=repr(v)):
                with self.assertRaises(ValidationError):
                    validate_api_key(v)


class FormTest(TestCase):
    def data(self, **kw):
        d = dict(name='n1', transfer='chemassistent', user='', password=KEY, src='/s', dst='https://cam.example',
                 shuttle_type='file', common_name_parts='^a', duration=300, architecture='ubuntu_64')
        d.update(kw)
        return d

    def form(self, files=None, **kw):
        return ShuttleInstanceForm(self.data(**kw), files or {})

    def test_valid_without_user(self):
        f = self.form()
        self.assertTrue(f.is_valid(), f.errors)

    def test_user_cleared(self):
        f = self.form(user='someone')
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['user'], '')

    def test_destinations(self):
        for dst in ('https://cam.example', 'https://cam.example/', 'https://cam.example/api/jobs/trigger'):
            with self.subTest(dst=dst):
                self.assertTrue(self.form(dst=dst).is_valid())
        for dst in ('ftp://cam.example', 'cam.example/p', 'https://'):
            with self.subTest(dst=dst):
                self.assertIn('dst', self.form(dst=dst).errors)

    def test_key_format(self):
        self.assertIn('password', self.form(password='no_prefix_' + 'x' * 30).errors)
        self.assertIn('password', self.form(password='cam_short').errors)
        self.assertIn('password', self.form(password='cam_' + 'x' * 10 + ' ' + 'x' * 10).errors)
        self.assertIn('password', self.form(password='cam_' + 'x' * 200).errors)

    def test_key_not_checked_for_other_transfers(self):
        f = self.form(transfer='webdav', user='u', password='pw')
        self.assertTrue(f.is_valid(), f.errors)

    def test_converter_rejected(self):
        f = self.form(files={'profile': SimpleUploadedFile('p.json', b'{}')}, with_converter='on',
                      architecture='win_64', dst_bagit='https://y.example/b', user_bagit='u', passwort_bagit='p',
                      public_link='https://p.example/')
        self.assertIn('with_converter', f.errors)
        self.assertIn('ChemAssistent', str(f.errors['with_converter']))

    def test_host_key_cleared(self):
        f = self.form(host_key='SHA256:' + 'A' * 43)
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['host_key'], '')
        f = self.form(host_key='garbage')
        self.assertTrue(f.is_valid(), f.errors)

    def test_xp_needs_no_host_key(self):
        self.assertTrue(self.form(architecture='win_i386').is_valid())

    def test_cert_and_insecure_allowed(self):
        f = self.form(files={'cert': SimpleUploadedFile('s.crt', make_pem())}, insecure='on')
        self.assertTrue(f.is_valid(), f.errors)
        self.assertNotIn('cert', f.errors)

    def test_user_required_for_webdav_and_sftp(self):
        for transfer, dst, extra in (('webdav', 'https://x.example/a', {}), ('sftp', 'host/p', {})):
            with self.subTest(transfer=transfer):
                f = self.form(transfer=transfer, dst=dst, user='', password='pw', host_key='', **extra)
                self.assertEqual(f.errors.get('user'), ['This field is required.'])
                f = self.form(transfer=transfer, dst=dst, user='   ', password='pw', host_key='', **extra)
                self.assertIn('user', f.errors)
                f = self.form(transfer=transfer, dst=dst, user='u', password='pw', host_key='', **extra)
                self.assertNotIn('user', f.errors)


class BuildConfigTest(TestCase):
    def inst(self, **kw):
        d = dict(name='c1', user='ignored', password=KEY, transfer='chemassistent', src='/s',
                 dst='https://cam.example', shuttle_type='folder', architecture='win_64')
        d.update(kw)
        return ShuttleInstance(**d)

    def test_config(self):
        cfg = self.inst(host_key='SHA256:' + 'A' * 43, with_converter=True, dst_bagit='b', user_bagit='bu',
                        passwort_bagit='bp', public_link='https://p/')._get_build_config()
        self.assertEqual(cfg['tType'], 'chemassistent')
        self.assertEqual(cfg['password'], KEY)
        self.assertEqual(cfg['user'], '')
        self.assertEqual(cfg['hostkey'], '')
        self.assertEqual(cfg['preconvert'], 'N')
        for k in ('dst_converter', 'user_converter', 'password_converter'):
            self.assertEqual(cfg[k], '', k)
        self.assertEqual(cfg['crt'], '')

    def test_password_escaped(self):
        raw = 'cam_&<>\'"\\' + 'x' * 20
        cfg = self.inst(password=raw)._get_build_config()
        value = cfg.dicts[-1]['password'] if hasattr(cfg, 'dicts') else cfg['password']
        self.assertEqual(json.loads('"' + value + '"'), raw)
        self.assertNotEqual(value, raw)  # the backslash and the quote are escaped

    def test_crt_with_cert(self):
        self.assertEqual(self.inst(cert='certs/x.crt')._get_build_config()['crt'], 'server.crt')
        self.assertEqual(self.inst()._get_build_config()['crt'], '')

    def test_insecure(self):
        self.assertEqual(self.inst(insecure=True)._get_build_config()['insecure'], '1')


class UsesTlsAndPackagingTest(TestCase):
    def inst(self, **kw):
        d = dict(name='c1', password=KEY, transfer='chemassistent', src='/s', dst='https://cam.example',
                 shuttle_type='file', architecture='win_i386')
        d.update(kw)
        return ShuttleInstance(**d)

    def test_uses_tls(self):
        self.assertTrue(self.inst(transfer='chemassistent').uses_tls())
        self.assertTrue(self.inst(transfer='webdav').uses_tls())
        self.assertFalse(self.inst(transfer='sftp').uses_tls())

    def test_only_exe(self):
        for arch in ('win_i386', 'win_64', 'ubuntu_64', 'raspberry_pi_6', 'raspberry_pi_7', 'raspberry_pi_64'):
            with self.subTest(arch=arch):
                self.assertTrue(self.inst(architecture=arch).only_exe())
                self.assertFalse(self.inst(architecture=arch, cert='certs/x.crt').only_exe())

    def test_only_exe_even_with_converter_flag(self):
        self.assertTrue(self.inst(architecture='win_64', with_converter=True).only_exe())
