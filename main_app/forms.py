from main_app.models import ElnUser
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from cryptography import x509

from main_app.validators import validate_host_key, validate_destination, destination_host_port, LINUX_USER_RE

from main_app.models import ShuttleInstance
from main_app.models import GitInstance
from main_app.models import ElnConnection
from django.forms.models import ModelForm
from django.forms import PasswordInput


# Form Model ElnConnection

class ElnConnectionForm(ModelForm):
    class Meta:
        model = ElnConnection
        fields = "__all__"



# Form Model GitInstance

class GitInstanceForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            self.fields['name'].widget.attrs['readonly'] = True


    def clean_name(self):
        instance = self.instance
        if instance and instance.pk:
            return instance.name
        else:
            return self.cleaned_data['name']


    class Meta:
        model = GitInstance
        fields = ['name', 'url', 'branch']

    def generate_filte(self):
        pass



# Form Model ShuttleInstance

class ShuttleInstanceForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            self.fields['name'].widget.attrs['readonly'] = True

    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return self.cleaned_data['name']

    def clean_public_link(self):
        val = self.cleaned_data['public_link']
        if val and len(val) > 0 and val[-1] != '/':
            val += '/'
        return val

    def clean_host_key(self):
        val = (self.cleaned_data.get('host_key') or '').strip()
        validate_host_key(val)
        return val

    def clean_linux_user(self):
        val = (self.cleaned_data.get('linux_user') or '').strip()
        if val and not LINUX_USER_RE.match(val):
            raise ValidationError(_('The Linux user must start with a lowercase letter or underscore and contain only lowercase letters, digits, "_" and "-" (max. 32 characters).'))
        return val

    def clean_cert(self):
        cert = self.cleaned_data.get('cert')
        # an already stored, unchanged file is not re-read
        if not cert or not hasattr(cert, 'read') or getattr(cert, '_committed', False) or cert is False:
            return cert
        if cert.size > 64 * 1024:
            raise ValidationError(_('The certificate file is too large (max. 64 KB).'))
        data = cert.read(64 * 1024 + 1)
        cert.seek(0)
        try:
            certs = x509.load_pem_x509_certificates(data)
        except Exception:
            certs = []
        if not certs:
            raise ValidationError(_('The file is not a PEM certificate.'))
        return cert

    def clean(self):
        cleaned_data = super().clean()
        transfer = cleaned_data.get('transfer')
        if str(cleaned_data.get('architecture') or '').startswith('win'):
            # linux_user doesn't apply to Windows: drop the value and any format error
            self._errors.pop('linux_user', None)
            cleaned_data['linux_user'] = ''
        with_converter = cleaned_data.get('with_converter')
        if with_converter:
            if cleaned_data.get('architecture') not in ['win_64', 'ubuntu_64']:
                self.add_error('with_converter', ValidationError(_('Converter can only be used for Architecture Windows 64 Bit and Ubuntu 64 Bit')))
            needed_fields_for_converter = ['dst_bagit', 'user_bagit', 'passwort_bagit', 'public_link', 'profile']
            for field in needed_fields_for_converter:
                field_val = cleaned_data.get(field)
                if not field_val:
                    self.add_error(field, ValidationError(
                        _('If "with converter" is checked then %(field)s must be set') % {'field': field}))

        if cleaned_data.get('shuttle_type') == 'flat_tar':
            common_name_parts = cleaned_data.get('common_name_parts') or ''
            if len(common_name_parts) == 0:
                self.add_error('common_name_parts', ValidationError(_('Common name regex must not be empty if the send type is set to flat_tar')))

            try:
                re.compile(fr"{common_name_parts}")
            except re.error:
                self.add_error('common_name_parts', ValidationError(_('Common name regex must be a compilable regular expression send type is set to flat_tar')))

        if transfer in ('webdav', 'sftp'):
            dst_ok = {}
            for field, active in (('dst', True), ('dst_bagit', bool(with_converter))):
                value = cleaned_data.get(field)
                if not active or not value or field in self.errors:
                    continue
                try:
                    validate_destination(value, transfer)
                    dst_ok[field] = value
                except ValidationError as e:
                    self.add_error(field, e)
            host_key = cleaned_data.get('host_key') or ''
            if transfer == 'webdav':
                cleaned_data['host_key'] = ''
            else:
                if cleaned_data.get('cert'):
                    self.add_error('cert', ValidationError(_('The certificate is only used for WebDAV.')))
                insecure = cleaned_data.get('insecure')
                if (cleaned_data.get('architecture') == 'win_i386' and not host_key and not insecure
                        and 'host_key' not in self.errors):
                    self.add_error('host_key', ValidationError(_(
                        'A host key is required for Windows i386 (XP) with SFTP, unless verification is disabled.')))
                if host_key and with_converter and len(dst_ok) == 2:
                    if destination_host_port(dst_ok['dst'], 'sftp') != destination_host_port(dst_ok['dst_bagit'], 'sftp'):
                        self.add_error('host_key', ValidationError(_(
                            'The pinned host key applies to both destinations; they must be the same server.')))
        return cleaned_data

    class Meta:
        model = ShuttleInstance
        fields = ['name', 'transfer', 'user', 'password', 'src', 'dst', 'shuttle_type', 'common_name_parts', 'duration', 'architecture', 'with_converter', 'dst_bagit', 'user_bagit', 'passwort_bagit', 'public_link', 'profile', 'host_key', 'cert', 'insecure', 'linux_user']
        # Password fields keep the stored value but are never read or filled by the AI assistant
        widgets = {
            'password': PasswordInput(render_value=True),
            'passwort_bagit': PasswordInput(render_value=True),
        }



# Form Model ElnUser

class ElnUserForm(ModelForm):
    class Meta:
        model = ElnUser
        fields = "__all__"
