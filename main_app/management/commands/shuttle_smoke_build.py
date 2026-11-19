"""Build smoke test: compiles Shuttle for all supported architectures and checks the results.

Run it inside the Docker image with a throw-away SQLite database (see `dev/smoke_build.sh`):

    DJANGO_DATABASE=jest python manage.py shuttle_smoke_build [--shuttle-src URL_OR_PATH] [--branch main]

The command refuses to run against any database other than SQLite and works in a fresh temporary directory.
Only dummy credentials are used; passwords are never printed.
"""
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from main_app.build import BuildError

DEFAULT_SRC = 'https://github.com/ComPlat/shuttle.git'
HOST_KEY = 'ssh-ed25519 255 SHA256:' + 'A' * 43

# Values that need escaping somewhere on the way into the Go source (same as the M1 smoke test).
NASTY = {
    'password': "p&a<s>s'\"\\",
    'user': "u&<'\"x",
    'src': 'C:\\Data & Results\\<raw>',
    'dst': 'https://example.invalid/dav/a&b/',
    'common_name_parts': r'^<a>\d+',
}

# architecture -> expected start of the output of `file <binary>`
FILE_EXPECT = {
    'ubuntu_64': 'ELF 64-bit LSB executable, x86-64',
    'raspberry_pi_6': 'ELF 32-bit LSB executable, ARM',
    'raspberry_pi_7': 'ELF 32-bit LSB executable, ARM',
    'raspberry_pi_64': 'ELF 64-bit LSB executable, ARM aarch64',
    'win_64': 'PE32+ executable',
    'win_i386': 'PE32 executable',
}

# -help flag -> field name used in the summary. `pass` is a secret and is never printed.
HELP_FLAGS = ('pass', 'user', 'src', 'dst', 'commonRegex', 'hostkey', 'insecure', 'crt')

# (label, architecture, transfer, extra fields, cert?)
CASES = [
    ('ubuntu_64', 'ubuntu_64', 'webdav', {}, False),
    ('raspberry_pi_6', 'raspberry_pi_6', 'sftp', {'host_key': HOST_KEY}, False),
    ('raspberry_pi_7', 'raspberry_pi_7', 'webdav', {}, False),
    ('raspberry_pi_64', 'raspberry_pi_64', 'sftp', {'host_key': HOST_KEY}, False),
    ('win_64', 'win_64', 'webdav', {}, False),
    ('win_i386', 'win_i386', 'sftp', {'host_key': HOST_KEY}, False),
    ('win_i386', 'win_i386', 'webdav', {}, False),
    ('ubuntu_64+insecure', 'ubuntu_64', 'sftp', {'host_key': HOST_KEY, 'insecure': True}, False),
    ('ubuntu_64+cert', 'ubuntu_64', 'webdav', {}, True),
]


def file_matches(architecture, file_output):
    """True if the output of `file <binary>` (with or without the leading "path: ") has the expected type."""
    expected = FILE_EXPECT.get(architecture)
    return bool(expected) and expected in file_output


def parse_help_defaults(help_text, flags=HELP_FLAGS):
    """Default values of Go `flag` options from `-help` text.

    A flag block is the flag's own line (`  -name type`) and all following lines up to the next flag line.
    A flag without `(default "...")` has the default "". Quoted values are Go `%q` strings.
    `None` means the flag is missing from the text or its value cannot be decoded.
    """
    blocks, current = {}, None
    for line in help_text.splitlines():
        m = re.match(r'^\s+-{1,2}(\w+)', line)
        if m:
            current = m.group(1)
            blocks[current] = line
        elif current:
            blocks[current] += '\n' + line
    result = {}
    for flag in flags:
        block = blocks.get(flag)
        if block is None:
            result[flag] = None
            continue
        m = re.search(r'\(default ("(?:[^"\\]|\\.)*")\)', block, re.S)
        if not m:
            result[flag] = ''
            continue
        try:
            result[flag] = json.loads(m.group(1))
        except ValueError:
            result[flag] = None
    return result


def expected_defaults(fields, has_cert):
    """The `-help` defaults a binary built from `fields` must show."""
    sftp = fields['transfer'] == 'sftp'
    return {
        'pass': fields['password'],
        'user': fields['user'],
        'src': fields['src'],
        'dst': fields['dst'],
        'commonRegex': fields['common_name_parts'],
        'hostkey': fields.get('host_key', '') if sftp else '',
        'insecure': '1' if fields.get('insecure') else '',
        'crt': 'server.crt' if (has_cert and not sftp) else '',
    }


def self_signed_pem():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'smoke')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
            .sign(key, hashes.SHA256()))
    return cert.public_bytes(serialization.Encoding.PEM)


def can_run_amd64():
    return platform.machine().lower() in ('x86_64', 'amd64')


class Command(BaseCommand):
    help = ('Builds Shuttle for all architectures from a Shuttle source and checks the binaries. '
            'Needs a throw-away SQLite database (DJANGO_DATABASE=jest). Exit code 1 if a case failed.')

    def add_arguments(self, parser):
        parser.add_argument('--shuttle-src', default=DEFAULT_SRC,
                            help='Git URL or local path of the Shuttle source (default: %(default)s).')
        parser.add_argument('--branch', default='main', help='Branch or commit (default: %(default)s).')
        parser.add_argument('--json', dest='json_path', default=None,
                            help='Write the results (without secrets) to this JSON file.')
        parser.add_argument('--keep', action='store_true', help='Keep the temporary working directory.')

    def handle(self, *args, **options):
        engine = settings.DATABASES['default']['ENGINE']
        if not engine.endswith('sqlite3'):
            raise CommandError('shuttle_smoke_build creates test data and works only with SQLite, but the default '
                               'database uses %s. Run it with DJANGO_DATABASE=jest.' % engine)

        json_path = os.path.abspath(options['json_path']) if options['json_path'] else None
        original_cwd = os.getcwd()
        workdir = tempfile.mkdtemp(prefix='shuttle_smoke_')
        os.chdir(workdir)
        try:
            results = self._run(options['shuttle_src'], options['branch'])
        finally:
            os.chdir(original_cwd)
            if options['keep']:
                self.stdout.write('Working directory kept: %s' % workdir)
            else:
                shutil.rmtree(workdir, ignore_errors=True)

        failed = [r for r in results if not r['ok']]
        self.stdout.write('SMOKE RESULT: %s (%d/%d cases OK)' % (
            'FAIL' if failed else 'PASS', len(results) - len(failed), len(results)))
        if json_path:
            with open(json_path, 'w') as f:
                json.dump({'ok': not failed, 'cases': results}, f, indent=2)
        if failed:
            raise SystemExit(1)

    def _run(self, src, branch):
        from main_app.models import GitInstance, ShuttleInstance
        User = get_user_model()
        owner, _ = User.objects.get_or_create(username='smoke')
        git, _ = GitInstance.objects.update_or_create(name='smoke', defaults={'url': src, 'branch': branch})
        git.set_active()
        try:
            git.git_reload()
        except Exception as e:
            self.stdout.write('FAIL git_reload: %s' % e)
            return [{'case': 'git_reload', 'ok': False, 'error': str(e)}]
        self.stdout.write('Shuttle source %s (%s), version %r' % (src, branch, git.shuttle_version))

        results = []
        for label, arch, transfer, extra, with_cert in CASES:
            name = 'smoke_%s_%s' % (label.replace('+', '_'), transfer)
            ShuttleInstance.objects.filter(name=name).delete()
            fields = dict(NASTY, transfer=transfer, **extra)
            if transfer == 'sftp' and 'host_key' in extra and arch == 'ubuntu_64':
                fields['dst'] = 'sftp.example.invalid:2222/data'
            inst = ShuttleInstance(name=name, architecture=arch, shuttle_type='file', owner=owner, duration=300,
                                   **fields)
            if with_cert:
                inst.cert.save('smoke.crt', ContentFile(self_signed_pem()), save=False)
            inst.save()
            result = self._check_case(label, arch, transfer, inst, fields, with_cert, git.shuttle_version)
            results.append(result)
            self._report(result)
            if with_cert and inst.cert:
                inst.cert.delete(save=False)
            inst.delete()
        return results

    def _check_case(self, label, arch, transfer, inst, fields, with_cert, git_version):
        from main_app.models import ShuttleInstance
        result = {'case': label, 'architecture': arch, 'transfer': transfer, 'ok': False, 'file': '', 'problems': []}
        try:
            path = inst.build()
        except BuildError as e:
            result['problems'].append('BuildError: %s (reference %s) %s' % (e.public_message, e.reference, e.detail))
            return result
        except Exception as e:
            result['problems'].append('%s: %s' % (type(e).__name__, getattr(e, 'detail', '') or e))
            return result

        if not path or not os.path.isfile(path):
            result['problems'].append('build() returned no existing file: %r' % (path,))
            return result
        try:
            out = subprocess.run(['file', '-b', path], capture_output=True, text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError) as e:
            out = ''
            result['problems'].append('file failed: %s' % e)
        result['file'] = out[:70]
        if not file_matches(arch, out):
            result['problems'].append('file type %r, expected %r' % (out[:70], FILE_EXPECT[arch]))

        built = ShuttleInstance.objects.filter(pk=inst.pk).values_list('built_version', flat=True).first()
        if built != git_version:
            result['problems'].append('built_version %r != Shuttle version %r' % (built, git_version))

        if arch == 'ubuntu_64' and can_run_amd64():
            try:
                help_text = subprocess.run([path, '-help'], capture_output=True, text=True, timeout=60).stderr
            except (OSError, subprocess.SubprocessError) as e:
                help_text = ''
                result['problems'].append('-help failed: %s' % e)
            got = parse_help_defaults(help_text)
            want = expected_defaults(fields, with_cert)
            wrong = [flag for flag in HELP_FLAGS if got.get(flag) != want[flag]]
            result['defaults_checked'] = list(HELP_FLAGS)
            if wrong:
                result['problems'].append('-help defaults differ for: ' + ', '.join(wrong))
        result['ok'] = not result['problems']
        return result

    def _report(self, r):
        self.stdout.write('%s %-20s %-7s %s' % ('OK  ' if r['ok'] else 'FAIL', r['case'], r.get('transfer', ''),
                                                 r.get('file', '')))
        if r.get('defaults_checked'):
            state = 'match' if r['ok'] or not any('defaults' in p for p in r['problems']) else 'DIFFER'
            self.stdout.write('     -help defaults (pass=***): %s' % state)
        for p in r['problems']:
            self.stdout.write('     ! %s' % p)
