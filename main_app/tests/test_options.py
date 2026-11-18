import os
import tempfile
from unittest import mock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
import datetime

from main_app.build import read_shuttle_version
from main_app.forms import ShuttleInstanceForm
from main_app.models import ShuttleInstance
from main_app.validators import validate_host_key, validate_destination

SHA = 'SHA256:' + 'A' * 43
MD5 = ':'.join(['0f'] * 16)


def make_pem():
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'test.example')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
            .sign(key, hashes.SHA256()))
    return cert.public_bytes(serialization.Encoding.PEM)


class HostKeyValidatorTest(SimpleTestCase):
    def test_valid(self):
        for v in [SHA, SHA + '=', 'ssh-ed25519 255 ' + SHA, '  ' + SHA + ' ', MD5, 'MD5:' + MD5, MD5.upper(), '']:
            validate_host_key(v)

    def test_invalid(self):
        for v in ['ssh-ed25519 255 ' + MD5, 'SHA256:' + 'A' * 42, 'SHA256:' + 'A' * 44, 'SHA256:' + '!' * 43,
                  ':'.join(['0f'] * 15), ':'.join(['zz'] * 16), 'garbage', 'sha256:' + 'A' * 43]:
            with self.assertRaises(ValidationError, msg=v):
                validate_host_key(v)


class DestinationValidatorTest(SimpleTestCase):
    def test_sftp_valid(self):
        for v in ['host/path', 'host:2222/path', 'ssh://host/p', 'SFTP://host:22/p', 'os-login.lsdf.kit.edu/kit/ioc/projects/x/',
                  'host', '[::1]:22/p']:
            validate_destination(v, 'sftp')

    def test_sftp_invalid(self):
        for v in ['', '   ', 'host:0/p', 'host:70000/p', 'host:abc/p', 'ssh:///path', '/path']:
            with self.assertRaises(ValidationError, msg=v):
                validate_destination(v, 'sftp')

    def test_webdav(self):
        validate_destination('https://x.example/a', 'webdav')
        validate_destination('http://x.example:8080/a', 'webdav')
        for v in ['x.example/a', 'ftp://x.example/', 'https:///a', 'ssh://x.example/', 'https://x:99999/']:
            with self.assertRaises(ValidationError, msg=v):
                validate_destination(v, 'webdav')


class VersionTest(SimpleTestCase):
    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_shuttle_version(d), '')
            self.assertEqual(read_shuttle_version(None), '')
            with open(os.path.join(d, 'main.go'), 'w', encoding='utf-8') as f:
                f.write('package main\n\n// shuttleVersion is x\nconst shuttleVersion = "1.14"\n')
            self.assertEqual(read_shuttle_version(d), '1.14')
            with open(os.path.join(d, 'main.go'), 'w', encoding='utf-8') as f:
                f.write('package main\n')
            self.assertEqual(read_shuttle_version(d), '')


class BuildConfigTest(SimpleTestCase):
    def inst(self, **kw):
        values = dict(name='i', user='u', password='pw', transfer='sftp', src='s', dst='h/p', shuttle_type='file',
                      architecture='ubuntu_64', host_key='  ' + SHA + ' ')
        values.update(kw)
        return ShuttleInstance(**values)

    def test_hostkey_insecure_crt(self):
        ctx = self.inst()._get_build_config()
        flat = {k: ctx[k] for k in ('hostkey', 'insecure', 'crt')} if isinstance(ctx, dict) else None
        if flat is None:
            flat = {k: ctx.get(k) for k in ('hostkey', 'insecure', 'crt')}
        self.assertEqual(flat, {'hostkey': SHA, 'insecure': '', 'crt': ''})
        flat = self.inst(insecure=True)._get_build_config()
        self.assertEqual(flat.get('insecure'), '1')
        wd = self.inst(transfer='webdav', cert='certs/x.crt')._get_build_config()
        self.assertEqual((wd.get('hostkey'), wd.get('crt')), ('', 'server.crt'))
        sf = self.inst(cert='certs/x.crt')._get_build_config()
        self.assertEqual(sf.get('crt'), '')

    def test_only_exe(self):
        self.assertTrue(self.inst(transfer='webdav', architecture='win_64').only_exe())
        self.assertFalse(self.inst(transfer='webdav', architecture='win_64', cert='certs/x.crt').only_exe())
        self.assertTrue(self.inst(architecture='win_64', cert='certs/x.crt').only_exe())
        self.assertFalse(self.inst(architecture='win_i386').only_exe())


class FormTest(TestCase):
    def data(self, **kw):
        d = dict(name='n1', transfer='sftp', user='u', password='pw', src='/s', dst='host/path', shuttle_type='file',
                 common_name_parts='^a', duration=300, architecture='ubuntu_64', host_key=SHA)
        d.update(kw)
        return d

    def form(self, files=None, **kw):
        return ShuttleInstanceForm(self.data(**kw), files or {})

    def test_valid(self):
        f = self.form()
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(self.form(host_key='  ' + SHA + '  ').errors.get('host_key'), None)

    def test_bad_host_key(self):
        self.assertIn('host_key', self.form(host_key='garbage').errors)

    def test_webdav_clears_host_key(self):
        f = self.form(transfer='webdav', dst='https://x.example/a')
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['host_key'], '')

    def test_xp_sftp(self):
        self.assertIn('host_key', self.form(architecture='win_i386', host_key='').errors)
        self.assertTrue(self.form(architecture='win_i386', host_key='', insecure='on').is_valid())
        self.assertTrue(self.form(architecture='win_i386').is_valid())

    def test_xp_webdav_no_key_needed(self):
        self.assertTrue(self.form(architecture='win_i386', transfer='webdav', host_key='',
                                  dst='https://x.example/').is_valid())

    def test_destination(self):
        self.assertIn('dst', self.form(dst='host:99999/p').errors)
        self.assertIn('dst', self.form(transfer='webdav', dst='host/p').errors)

    def test_duration(self):
        self.assertIn('duration', self.form(duration=0).errors)

    def conv(self, **kw):
        d = dict(with_converter='on', architecture='win_64', dst_bagit='other/p', user_bagit='u', passwort_bagit='p',
                 public_link='https://p.example/')
        d.update(kw)
        return d

    def test_converter_host_key(self):
        pr = SimpleUploadedFile('p.json', b'{}')
        f = self.form(files={'profile': pr}, **self.conv())
        self.assertIn('host_key', f.errors)
        pr = SimpleUploadedFile('p.json', b'{}')
        f = self.form(files={'profile': pr}, **self.conv(dst_bagit='host:22/other'))
        self.assertNotIn('host_key', f.errors, f.errors)
        pr = SimpleUploadedFile('p.json', b'{}')
        f = self.form(files={'profile': pr}, **self.conv(host_key=''))
        self.assertNotIn('host_key', f.errors)

    def test_converter_dst_bagit_validated(self):
        pr = SimpleUploadedFile('p.json', b'{}')
        f = self.form(files={'profile': pr}, **self.conv(dst_bagit='host:0/x', host_key=''))
        self.assertIn('dst_bagit', f.errors)

    def test_cert(self):
        pem = make_pem()
        f = self.form(transfer='webdav', dst='https://x.example/a',
                      files={'cert': SimpleUploadedFile('s.crt', pem)})
        self.assertTrue(f.is_valid(), f.errors)
        f = self.form(transfer='webdav', dst='https://x.example/a',
                      files={'cert': SimpleUploadedFile('s.crt', b'not a cert')})
        self.assertIn('cert', f.errors)
        f = self.form(transfer='webdav', dst='https://x.example/a',
                      files={'cert': SimpleUploadedFile('s.crt', b'x' * (64 * 1024 + 1))})
        self.assertIn('cert', f.errors)
        f = self.form(transfer='webdav', dst='https://x.example/a',
                      files={'cert': SimpleUploadedFile('s.txt', pem)})
        self.assertIn('cert', f.errors)

    def test_cert_with_sftp(self):
        f = self.form(files={'cert': SimpleUploadedFile('s.crt', make_pem())})
        self.assertIn('cert', f.errors)

    def test_stored_cert_not_reread(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            user = None
            inst = ShuttleInstance(name='n1', user='u', password='pw', transfer='webdav', src='/s',
                                   dst='https://x.example/a', shuttle_type='file', architecture='ubuntu_64')
            inst.cert.save('s.crt', SimpleUploadedFile('s.crt', b'garbage'), save=False)
            f = ShuttleInstanceForm(self.data(transfer='webdav', dst='https://x.example/a', host_key=''),
                                    {}, instance=inst)
            self.assertNotIn('cert', f.errors)


class VersionStorageTest(TestCase):
    def test_git_reload_and_build_store_versions(self):
        from main_app.models import GitInstance
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            os.chdir(d)
            try:
                git = GitInstance.objects.create(name='g', url='u', branch='main', is_active=True)

                def fake_run(cmd, cwd=None, **kw):
                    if cmd[:2] == ['git', 'clone']:
                        os.makedirs(os.path.join(cwd, 'repo'))
                        with open(os.path.join(cwd, 'repo', 'main.go'), 'w') as f:
                            f.write('const shuttleVersion = "9.9"\n')
                    return mock.Mock(returncode=0, stdout='', stderr='')
                with mock.patch('main_app.models.subprocess.run', side_effect=fake_run):
                    git.git_reload()
                git.refresh_from_db()
                self.assertEqual(git.shuttle_version, '9.9')
            finally:
                os.chdir(cwd)
