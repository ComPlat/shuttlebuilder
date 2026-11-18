"""Validators for the Shuttle options (M3). They mirror Shuttle's own parsing
(`parseDst` in cmd_manager.go, `fingerprintMatches` in ssh_hostkey.go)."""
import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

_SHA256 = re.compile(r'^(?:\S+ \d+ )?SHA256:[A-Za-z0-9+/]{43}=?$')
_MD5 = re.compile(r'^(?:MD5:)?[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){15}$')
# Linux user names accepted for the systemd unit (User=); shared by the form and the unit renderer.
LINUX_USER_RE = re.compile(r'^[a-z_][a-z0-9_-]{0,31}\Z')


def validate_host_key(value):
    """Accept `SHA256:<43 base64>`, WinSCP style `ssh-ed25519 255 SHA256:<...>` or MD5 `aa:bb:...` (optional `MD5:`)."""
    value = (value or '').strip()
    if not value:
        return
    if _SHA256.match(value) or _MD5.match(value):
        return
    raise ValidationError(_('Invalid host key fingerprint. Use "SHA256:<base64>" (optionally preceded by the '
                            'algorithm and bits, e.g. "ssh-ed25519 255 SHA256:..."), or an MD5 fingerprint '
                            '"aa:bb:...:ff" (16 hex pairs, optionally prefixed "MD5:").'),
                          code='invalid_host_key')


def validate_destination(value, transfer):
    """Check a destination like Shuttle's parseDst. Raises ValidationError."""
    value = (value or '').strip()
    if not value:
        raise ValidationError(_('The destination must not be empty.'), code='invalid_destination')
    try:
        if transfer == 'sftp':
            if not re.match(r'^(ssh|sftp)://', value, re.IGNORECASE):
                value = 'ssh://' + value
            parts = urlsplit(value)
            host = parts.hostname
            port = parts.port
        elif transfer == 'webdav':
            parts = urlsplit(value)
            if parts.scheme.lower() not in ('http', 'https'):
                raise ValidationError(_('A WebDAV destination must start with http:// or https://.'),
                                      code='invalid_destination')
            host = parts.hostname
            port = parts.port
        else:
            return
    except ValueError:
        raise ValidationError(_('The destination is not a valid address (check the host and the port).'),
                              code='invalid_destination')
    if not host:
        raise ValidationError(_('The destination has no host.'), code='invalid_destination')
    if port is not None and not 1 <= port <= 65535:
        raise ValidationError(_('The port must be between 1 and 65535.'), code='invalid_destination')


def destination_host_port(value, transfer):
    """(host, port) of a destination (already validated); port defaults to 22 for SFTP, 80/443 for WebDAV."""
    value = (value or '').strip()
    if transfer == 'sftp':
        if not re.match(r'^(ssh|sftp)://', value, re.IGNORECASE):
            value = 'ssh://' + value
        default = 22
    else:
        default = 443 if value.lower().startswith('https') else 80
    parts = urlsplit(value)
    return (parts.hostname or '').lower(), parts.port or default
