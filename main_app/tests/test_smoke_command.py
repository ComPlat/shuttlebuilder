import io
import os
import tempfile
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from main_app.build import BuildError
from main_app.management.commands import shuttle_smoke_build as smoke
from main_app.models import GitInstance, ShuttleInstance

HELP_SAMPLE = '''Usage of shuttle:
  -commonRegex string
    	Regex, e.g. "^a" (default "^<a>\\\\d+")
  -crt string
    	Server certificate
    	(default "server.crt")
  -dst string
    	Target with a "quoted" word and
    	more usage text (default "https://example.invalid/a\\"b\\\\c/")
  -hostkey string
    	Host key
  -insecure string
    	Skip checks
  -pass string
    	Password (default "p&a<s>s'\\"\\\\")
  -user string
    	User (default "u")
'''


class SqliteGuardTest(SimpleTestCase):
    def test_refuses_postgres(self):
        dbs = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'x'}}
        with override_settings(DATABASES=dbs):
            with self.assertRaises(CommandError) as cm:
                call_command('shuttle_smoke_build', stdout=io.StringIO())
        self.assertIn('DJANGO_DATABASE=jest', str(cm.exception))


class HelpParserTest(SimpleTestCase):
    def test_parse(self):
        got = smoke.parse_help_defaults(HELP_SAMPLE, ('commonRegex', 'crt', 'dst', 'hostkey', 'insecure', 'pass',
                                                       'user', 'src'))
        self.assertEqual(got['commonRegex'], '^<a>\\d+')
        self.assertEqual(got['crt'], 'server.crt')  # default on a continuation line
        self.assertEqual(got['dst'], 'https://example.invalid/a"b\\c/')  # \" and \\ decoded
        self.assertEqual(got['hostkey'], '')  # no default -> empty
        self.assertEqual(got['insecure'], '')
        self.assertEqual(got['pass'], 'p&a<s>s\'"\\')
        self.assertEqual(got['user'], 'u')
        self.assertIsNone(got['src'])  # flag missing

    def test_default_does_not_leak_into_next_flag(self):
        got = smoke.parse_help_defaults(HELP_SAMPLE, ('hostkey',))
        self.assertEqual(got['hostkey'], '')


class FileMatcherTest(SimpleTestCase):
    def test_table(self):
        good = {
            'ubuntu_64': 'ELF 64-bit LSB executable, x86-64, version 1 (SYSV)',
            'raspberry_pi_6': 'ELF 32-bit LSB executable, ARM, EABI5 version 1',
            'raspberry_pi_7': 'ELF 32-bit LSB executable, ARM, EABI5 version 1',
            'raspberry_pi_64': 'ELF 64-bit LSB executable, ARM aarch64, version 1',
            'win_64': 'PE32+ executable (console) x86-64, for MS Windows',
            'win_i386': 'PE32 executable (console) Intel 80386, for MS Windows',
        }
        for arch, text in good.items():
            with self.subTest(arch=arch):
                self.assertTrue(smoke.file_matches(arch, text))
                self.assertTrue(smoke.file_matches(arch, '/tmp/x: ' + text))
        self.assertFalse(smoke.file_matches('win_i386', good['win_64']))
        self.assertFalse(smoke.file_matches('ubuntu_64', good['raspberry_pi_64']))
        self.assertFalse(smoke.file_matches('raspberry_pi_6', good['raspberry_pi_64']))
        self.assertFalse(smoke.file_matches('unknown', good['win_64']))
        self.assertFalse(smoke.file_matches('win_64', 'ASCII text'))


class DryRunTest(TestCase):
    """Whole command with git, build and subprocess mocked; nothing is cloned or compiled."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.media = override_settings(MEDIA_ROOT=os.path.join(self.tmp.name, 'media'))
        self.media.enable()
        self.addCleanup(self.media.disable)
        self.binary = os.path.join(self.tmp.name, 'shuttle')
        with open(self.binary, 'wb') as f:
            f.write(b'fake')
        self.cwd = os.getcwd()
        self.addCleanup(os.chdir, self.cwd)

    @staticmethod
    def fake_reload(git):
        git.shuttle_version = '9.9.9'
        git.save()

    def fake_build(self, inst):
        ShuttleInstance.objects.filter(pk=inst.pk).update(built_version='9.9.9')
        return self.binary

    def fake_run(self, args, **kwargs):
        out = mock.Mock(returncode=0, stdout='', stderr='')
        if args[0] == 'file':
            arch = self.current_arch
            out.stdout = smoke.FILE_EXPECT[arch] + ', fake\n'
        return out

    def run_command(self, machine, build=None, run=None, extra_args=()):
        out = io.StringIO()
        ctx_build = build or mock.patch.object(ShuttleInstance, 'build', autospec=True, side_effect=self.fake_build)

        def tracking_build(inst):
            self.current_arch = inst.architecture
            return self.fake_build(inst)

        if build is None:
            ctx_build = mock.patch.object(ShuttleInstance, 'build', autospec=True, side_effect=tracking_build)
        with ctx_build, \
                mock.patch.object(GitInstance, 'git_reload', autospec=True, side_effect=self.fake_reload), \
                mock.patch.object(smoke.subprocess, 'run', side_effect=run or self.fake_run), \
                mock.patch.object(smoke.platform, 'machine', return_value=machine):
            code = 0
            try:
                call_command('shuttle_smoke_build', *extra_args, stdout=out)
            except SystemExit as e:
                code = e.code
        return code, out.getvalue()

    def test_all_ok_non_amd64(self):
        code, output = self.run_command('aarch64')
        self.assertEqual(code, 0, output)
        self.assertEqual(output.count('OK  '), len(smoke.CASES))
        self.assertIn('SMOKE RESULT: PASS', output)
        for secret in (smoke.NASTY['password'], 'p&a<s>s'):
            self.assertNotIn(secret, output)
        self.assertEqual(os.getcwd(), self.cwd)

    def test_build_error_fails_and_json_has_no_secret(self):
        json_path = os.path.join(self.tmp.name, 'result.json')
        err = BuildError('Build failed', detail='compiler said no', reference='abc123')
        build = mock.patch.object(ShuttleInstance, 'build', autospec=True, side_effect=err)
        code, output = self.run_command('aarch64', build=build, extra_args=('--json', json_path))
        self.assertEqual(code, 1)
        self.assertIn('FAIL', output)
        self.assertIn('Build failed', output)
        self.assertIn('abc123', output)
        self.assertIn('compiler said no', output)
        self.assertIn('SMOKE RESULT: FAIL', output)
        with open(json_path) as f:
            content = f.read()
        self.assertIn('"ok": false', content)
        self.assertNotIn(smoke.NASTY['password'], content)

    def test_defaults_checked_on_amd64_without_password_in_output(self):
        def run(args, **kwargs):
            if args[0] == 'file':
                return self.fake_run(args, **kwargs)
            # a wrong binary: nothing matches
            return mock.Mock(returncode=0, stdout='', stderr='Usage:\n  -user string\n    \tUser (default "x")\n')
        code, output = self.run_command('x86_64', run=run)
        self.assertEqual(code, 1)
        self.assertIn('-help defaults differ', output)
        self.assertNotIn(smoke.NASTY['password'], output)

    def test_defaults_match_on_amd64(self):
        def run(args, **kwargs):
            if args[0] == 'file':
                return self.fake_run(args, **kwargs)
            inst = ShuttleInstance.objects.get(architecture='ubuntu_64', name=self.current_name)
            has_cert = bool(inst.cert)
            fields = {k: getattr(inst, k) for k in ('password', 'user', 'src', 'dst', 'common_name_parts',
                                                    'transfer', 'host_key', 'insecure')}
            want = smoke.expected_defaults(fields, has_cert)
            text = 'Usage of shuttle:\n'
            for flag, value in want.items():
                text += '  -%s string\n    \tusage\n' % flag
                if value != '':
                    quoted = '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
                    text += '    \t(default %s)\n' % quoted
            return mock.Mock(returncode=0, stdout='', stderr=text)

        def build(inst):
            self.current_arch = inst.architecture
            self.current_name = inst.name
            return self.fake_build(inst)

        patch_build = mock.patch.object(ShuttleInstance, 'build', autospec=True, side_effect=build)
        code, output = self.run_command('x86_64', build=patch_build, run=run)
        self.assertEqual(code, 0, output)
        self.assertIn('-help defaults (pass=***): match', output)
