"""Plain text installation instructions (INSTALL.txt) that ship in every Shuttle zip.

The text never contains secrets: no password, user, token, host key or destination.
"""
import re

from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _

WIN_DIR = 'C:\\Program Files\\Shuttle'
LINUX_DIR = '/opt/Shuttle'
_CONTROL = re.compile(r'[\x00-\x1f\x7f]+')


def _clean(value):
    """One line of plain text: control characters (and so line breaks) become a space."""
    return _CONTROL.sub(' ', str(value)).strip()


def _url(request, name, **kwargs):
    return request.build_absolute_uri(reverse(name, kwargs=kwargs or None))


def _unit_url(instance, request):
    try:
        return _url(request, 'file_shuttle_instance.service', pk=instance.pk)
    except NoReverseMatch:
        return _url(request, 'file_shuttle.service')


def render_install_txt(instance, request):
    """Return INSTALL.txt for the zip of `instance` (CRLF line endings for Windows architectures)."""
    windows = instance.architecture.startswith('win')
    xp_sftp = instance.architecture == 'win_i386' and instance.transfer == 'sftp'
    exe = 'shuttle.exe' if windows else 'shuttle'
    install_dir = WIN_DIR if windows else LINUX_DIR
    folder = ('%USERPROFILE%\\shuttle\\shuttle_' + _clean(instance.name) + '\\') if windows \
        else '~/shuttle/shuttle_' + _clean(instance.name) + '/'
    register = folder + 'sent_register.json'
    log = folder + 'shuttle_log.txt'
    arch = instance.get_architecture_display() if hasattr(instance, 'get_architecture_display') \
        else instance.architecture
    transfer = instance.get_transfer_display() if hasattr(instance, 'get_transfer_display') else instance.transfer

    lines = [
        _('Shuttle installation'),
        '====================',
        '',
        _('Name: %(name)s') % {'name': _clean(instance.name)},
        _('Architecture: %(arch)s') % {'arch': _clean(arch)},
        _('Transfer: %(transfer)s') % {'transfer': _clean(transfer)},
        _('Shuttle version: %(version)s') % {'version': _clean(instance.built_version) or _('unknown')},
        '',
        _('Installation (administrator rights are required)'),
        '------------------------------------------------',
    ]
    if windows:
        lines += [
            _('1. Create the folder "%(dir)s".') % {'dir': install_dir},
            _('2. Copy ALL files of this zip (except INSTALL.txt) into "%(dir)s".') % {'dir': install_dir},
            _('3. Download %(url)s and copy the file shuttle_task.vbs into the startup folder '
              '(press Windows key + R, type shell:startup).') % {'url': _url(request, 'shuttle_task.vbs')},
            _('4. Restart the computer, or double-click shuttle_task.vbs once.'),
        ]
        if xp_sftp:
            lines += [
                '',
                _('Windows XP with SFTP: WinSCP.com and WinSCP.exe must stay in the same folder as shuttle.exe. '
                  'The SSH host key of the server is compiled into shuttle.exe.'),
            ]
    else:
        unit = _unit_url(instance, request)
        executables = ' '.join('%s/%s' % (install_dir, f)
                               for f in (['shuttle', 'ChemConverterApp'] if instance.with_converter else ['shuttle']))
        lines += [
            _('1. Create the folder "%(dir)s".') % {'dir': install_dir},
            _('2. Copy ALL files of this zip (except INSTALL.txt) into "%(dir)s" and make the programs executable '
              '(chmod +x %(files)s).') % {'dir': install_dir, 'files': executables},
            _('3. Download the systemd unit %(url)s (you have to be logged in) and save it as '
              '/etc/systemd/system/shuttle.service.') % {'url': unit},
            _('   If the file contains User=CHANGE_ME, replace CHANGE_ME with the Linux user that runs Shuttle.'),
            _('4. Run:'),
            '     systemctl daemon-reload',
            '     systemctl enable --now shuttle.service',
        ]
    if instance.cert and instance.transfer == 'webdav':
        lines += [
            '',
            _('server.crt is the certificate of the server. It must stay next to %(exe)s.') % {'exe': exe},
        ]
    lines += [
        '',
        _('Working folder, log and first start'),
        '-------------------------------------',
        _('Shuttle creates the working folder %(folder)s') % {'folder': folder},
        _('It holds the log (%(log)s), the list of sent files (sent_register.json) and, for SFTP, known_hosts.')
        % {'log': log},
        _('On the first start Shuttle sends every stable file that is already in the source folder once.'),
        _('To send everything again, stop Shuttle, delete %(register)s and start Shuttle again.')
        % {'register': register},
        _('Shuttle exits on configuration errors and prints the reason to the console, not to the log '
          '(Linux: journalctl -u shuttle.service). On Linux it stops cleanly on SIGTERM.'),
        '',
    ]
    return ('\r\n' if windows else '\n').join(lines)
