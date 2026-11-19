import glob
import os
import re
import shutil
import subprocess
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.utils import timezone
from sdc_core.sdc_extentions.models import SdcModel
from sdc_core.sdc_extentions.forms import AbstractSearchForm
from django.template.loader import render_to_string
from sdc_core.sdc_extentions.search import handle_search_form
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import signals
from main_app.build import read_shuttle_version, go_str, make_context, file_lock, compile_into_temp, build_timeout

User = get_user_model()


def create_user(sender, instance, created, **kwargs):
    """Create ElnUser for every new User."""
    if created:
        ElnUser.objects.create(user=instance)


signals.post_save.connect(create_user, sender=User, weak=False,
                          dispatch_uid='models.create_eln_user_profile')





class ElnUser(models.Model, SdcModel):
    """
    Per-user profile that records whether a user logs in through the connected Chemotion ELN.

    - One record per Django `User` (`user`, one-to-one); created automatically when a user is created.
    - `is_eln_user`: `true` if the last login was verified by the active `ElnConnection`, `false` for a local account login.
    - `token`: Chemotion API token from the last ELN login; empty for local logins.
    - Both fields are set by the login process, not by the user.
    - Each user can only read their own record; deleting the `User` deletes it.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, default='')
    is_eln_user = models.BooleanField(default=False)

    class SearchForm(AbstractSearchForm):
        """A default search form used in the list view. You can delete it if you dont need it"""
        CHOICES = (("id", "Id"),)
        PLACEHOLDER = ""
        DEFAULT_CHOICES = CHOICES[0][0]
        SEARCH_FIELDS = ("id",)

    class _SdcMeta:
        """Meta data information needed to manage all SDC operations."""
        edit_form = "main_app.forms.ElnUserForm"
        create_form = "main_app.forms.ElnUserForm"
        html_list_template = "main_app/models/ElnUser/ElnUser_list.html"
        html_detail_template = "main_app/models/ElnUser/ElnUser_details.html"

    @classmethod
    def render(cls, template_name, context=None, request=None, using=None):
        if template_name == getattr(cls.SdcMeta, 'html_list_template'):
            sf = cls.SearchForm(data=context.get("filter", {}))
            context = context | handle_search_form(context["instances"], sf,  range=10)
        return render_to_string(template_name=template_name, context=context, request=request, using=using)

    @classmethod
    def is_authorised(cls, user, action, obj):
        return True

    @classmethod
    def get_queryset(cls, user, action, obj):
        return cls.objects.filter(user=user)


# Create your models here.

class ElnConnectionSearchForm(AbstractSearchForm):
    CHOICES = (("url", "Url"), ("active", "Active"),)
    PLACEHOLDER = ""
    DEFAULT_CHOICES = CHOICES[0][0]
    SEARCH_FIELDS = ("url",)


class ElnConnection(models.Model, SdcModel):
    """
    Connection to a Chemotion ELN server whose accounts may log in to the ShuttleBuilder.

    - `url`: base URL of the Chemotion instance; `active`: only the active connection is used for login.
    - `token`, `device`: optional Chemotion API token and device id for this connection.
    - If no connection is active and the setting `ELN_URL` exists, an active connection to it is created automatically.
    - Users who log in with Chemotion credentials get a local account; new ones become staff if they are Chemotion admins.
    - Managed in the Django admin (`/admin/main_app/elnconnection/`); saving one as active deactivates all others.
    - `<shuttle-login>` shows the active connection's URL.
    """
    edit_form = "main_app.forms.ElnConnectionForm"
    create_form = "main_app.forms.ElnConnectionForm"
    html_list_template = "main_app/models/ElnConnection/ElnConnection_list.html"
    html_detail_template = "main_app/models/ElnConnection/ElnConnection_details.html"

    url = models.URLField(_('Eln connection!'))
    active = models.BooleanField()
    token = models.CharField(default=None, null=True, blank=True, max_length=255)
    device = models.IntegerField(default=0)

    def identifier(self):
        return f'URL: {self.url}'

    @classmethod
    def render(cls, template_name, context=None, request=None, using=None):
        if template_name == getattr(cls.SdcMeta, 'html_list_template'):
            sf = ElnConnectionSearchForm(data=context.get("filter", {}))
            context = context | handle_search_form(context["instances"], sf, range=10)
        return render_to_string(template_name=template_name, context=context, request=request, using=using)

    @classmethod
    def is_authorised(cls, user, action, obj):
        return True

    @classmethod
    def get_queryset(cls, user, action, obj):
        return cls.objects.all()

    @classmethod
    def get_active(cls):
        try:
            return ElnConnection.objects.get(active=True)
        except ElnConnection.MultipleObjectsReturned:
            keep = ElnConnection.objects.filter(active=True).order_by('-pk').first()
            ElnConnection.objects.filter(active=True).exclude(pk=keep.pk).update(active=False)
            return keep
        except ElnConnection.DoesNotExist:
            if hasattr(settings, 'ELN_URL'):
                return ElnConnection.objects.create(active=True, url=settings.ELN_URL)
        return None


class GitInstanceSearchForm(AbstractSearchForm):
    CHOICES = (("url", "Url"), ("branch", "Branch"),)
    PLACEHOLDER = ""
    DEFAULT_CHOICES = CHOICES[0][0]
    SEARCH_FIELDS = ("url", "branch")


class GitInstance(models.Model, SdcModel):
    """
    A git repository (and branch or commit) holding the Shuttle source code that executables are built from.

    - `name`: unique, cannot be changed later; `url`: clone URL; `branch`: branch name or commit id (default `main`).
    - `is_active`: exactly one repo is active; all Shuttle builds use it. Activating a repo makes it the source of every later build.
    - `last_reload`: when the repo was last cloned (`git clone`, then `git checkout <branch>`); `null` means it is cloned on the next build. A failed clone or checkout raises an error and keeps the previous checkout.
    - `shuttle_version`: version of the Shuttle in the checkout (`shuttleVersion` in `main.go`), read after every successful reload; empty if it cannot be found. Shown in the git list (`<git-instance-list>`), also as the version a download will build (tooltip of the download button in the Shuttle list).
    - If none is active, the default `ComPlat/shuttle/Main` (https://github.com/ComPlat/shuttle.git, `main`) is created and activated.
    - Rolling out a new Shuttle version: reload the active repo (or activate another one). Afterwards every `ShuttleInstance` is rebuilt on its next download (its `built_version` then shows the new version); the lab downloads the Shuttle again, replaces the executable and restarts it. Already installed Shuttles are not updated by themselves.
    - Builds use the toolchains of the server image: Go 1.26.11, and Go 1.10.8 (`XP_GOROOT`) for Windows i386 (Windows XP).
    - Readable and editable by every logged-in user.
    - Listed and activated in `<git-instance-list>`, created/edited in `<git-insatnce-edit>`.
    """
    edit_form = "main_app.forms.GitInstanceForm"
    create_form = "main_app.forms.GitInstanceForm"
    html_list_template = "main_app/models/GitInstance/GitInstance_list.html"
    html_detail_template = "main_app/models/GitInstance/GitInstance_details.html"
    name = models.CharField(help_text=_('Unique name of the git repo. This name cannot be changed!'), unique=True,
                            max_length=50)
    url = models.CharField(help_text=_('URL to the git repo.'), default='', max_length=255)
    branch = models.CharField(_('Commit Or Branch'), help_text=_('Enter the branch name or commit ID.'), max_length=255,
                              default='main')
    is_active = models.BooleanField(default=False)
    last_reload = models.DateTimeField(null=True, blank=True)
    shuttle_version = models.CharField(_('Shuttle version'), max_length=20, blank=True, default='',
                                       help_text=_('Version of the Shuttle in this checkout (read from main.go after each reload). Instances are rebuilt with it on their next download.'))

    def __str__(self):
        return self.name

    def get_path(self):
        folder_name = re.sub(r'[^a-zA-Z0-9]', '_', self.name)
        file_paths = os.path.join('./projects/git_repos/', folder_name)
        new_repo = glob.glob(os.path.join(file_paths, '*'))
        if len(new_repo) > 0:
            new_repo = os.path.abspath(new_repo[0])
        else:
            new_repo = None

        return (file_paths, new_repo)

    @classmethod
    def get_active(self):
        try:
            return GitInstance.objects.get(is_active=True)
        except GitInstance.MultipleObjectsReturned:
            GitInstance.objects.filter(is_active=True).update(is_active=False)
        except GitInstance.DoesNotExist:
            pass
        main_instance, c = GitInstance.objects.get_or_create(name='ComPlat/shuttle/Main')
        if c:
            main_instance.url = 'https://github.com/ComPlat/shuttle.git'
            main_instance.branch = 'main'
        main_instance.is_active = True
        main_instance.last_reload = None
        main_instance.save()
        return main_instance

    def set_active(self):
        GitInstance.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True
        self.save()

    def git_reload(self):
        file_paths, x = self.get_path()
        parent = os.path.dirname(os.path.abspath(file_paths))
        os.makedirs(parent, exist_ok=True)
        with file_lock(os.path.join(parent, ".lock")):
            tmp = tempfile.mkdtemp(prefix=".%s.tmp-" % os.path.basename(file_paths), dir=parent)
            try:
                try:
                    p = subprocess.run(['git', 'clone', self.url], cwd=tmp, capture_output=True, text=True,
                                       timeout=build_timeout())
                    cloned = p.returncode == 0
                except (subprocess.TimeoutExpired, OSError):
                    cloned = False
                if not cloned:
                    raise Exception(_("Url cannot be cloned: %s") % self.url)
                repos = glob.glob(os.path.join(tmp, '*'))
                repo = os.path.abspath(repos[0]) if repos else tmp
                try:
                    p = subprocess.run(['git', 'checkout', self.branch], cwd=repo, capture_output=True, text=True,
                                       timeout=build_timeout())
                    checked_out = p.returncode == 0
                except (subprocess.TimeoutExpired, OSError):
                    checked_out = False
                if not checked_out:
                    raise Exception(_("Branch or ID cannot be checked out: %s") % self.branch)
                for f in glob.glob(os.path.join(tmp, '*', '.git')) + glob.glob(os.path.join(tmp, '*', 'bin')):
                    shutil.rmtree(f, ignore_errors=True)
                shutil.rmtree(file_paths, ignore_errors=True)
                os.rename(tmp, file_paths)
                tmp = None
            finally:
                if tmp:
                    shutil.rmtree(tmp, ignore_errors=True)

        self.last_reload = timezone.now()
        self.shuttle_version = read_shuttle_version(self.get_path()[1])
        self.save()

    @classmethod
    def render(cls, template_name, context=None, request=None, using=None):
        if template_name == getattr(cls.SdcMeta, 'html_list_template'):
            sf = GitInstanceSearchForm(data=context.get("filter", {}))
            context = context | handle_search_form(context["instances"], sf, range=10)
        return render_to_string(template_name=template_name, context=context, request=request, using=using)

    @classmethod
    def is_authorised(cls, user, action, obj):
        return True

    @classmethod
    def get_queryset(cls, user, action, obj):
        return cls.objects.all()


class ShuttleInstanceSearchForm(AbstractSearchForm):
    CHOICES = (
        ('name', _('Name')), ('user', _('User')), ('shuttle_type', _('Type')), ('src', _('Source')),
        ('dst', _('Destination')),
        ('architecture', _('Architecture')))
    PLACEHOLDER = _('Name, Type, Source, Destination')
    DEFAULT_CHOICES = CHOICES[0][0]
    SEARCH_FIELDS = ('name', 'user', 'shuttle_type', 'src', 'dst', 'architecture')


TYPE_CHOISES = (
    ('file', _('File')),
    ('folder', _('Folder')),
    ('zip', _('ZIP')),
    ('tar', _('TAR')),
    ('flat_tar', _('Flat TAR'))
)

SYSTEM_CHOISES = (
    ('win_i386', _('Windows i386')),
    ('win_64', _('Windows 64 Bit')),
    ('ubuntu_64', _('Ubuntu 64 Bit')),
    ('raspberry_pi_6', _('Raspberry Pi ARMv6')),
    ('raspberry_pi_7', _('Raspberry Pi ARMv7')),
    ('raspberry_pi_64', _('Raspberry Pi ARM 64 Bit')),
)
TRANSFER_CHOISES = (
    ('webdav', _('WebDAV')),
    ('sftp', _('SFTP')),
    ('chemassistent', _('ChemAssistent job (HTTP upload)')),
)


class ShuttleInstance(models.Model, SdcModel):
    """
    Configuration of one Shuttle: a small program for a lab PC that watches a folder and uploads new data (WebDAV or SFTP).

    Fields:
    - `name`: unique, cannot be changed later; also the name of the working folder `~/shuttle/shuttle_<name>/` on the lab PC. `owner`: the creating user. Logged-in users see and change only their own instances; staff and superusers see all.
    - `src`: folder to watch on the lab PC (entered plainly, no doubled backslashes); `duration`: seconds a file must stay unchanged before it is sent (default 300, at least 1; it is also the longest wait between retries).
    - `transfer`: `webdav` or `sftp`; `dst`, `user`, `password`: target URL and credentials on the server. `dst` is checked: SFTP `host[:port]/path` (also `ssh://` or `sftp://`, port 22 by default), WebDAV `http(s)://host/path`.
    - `shuttle_type`: `file` (each file), `folder` (whole folder once complete), `zip` / `tar` (folder as an archive once complete) or `flat_tar` (files grouped by the `common_name_parts` regex into .tar.gz archives). A changed folder is sent again completely.
    - `architecture`: target system: `win_i386` (also Windows XP), `win_64`, `ubuntu_64`, `raspberry_pi_6`, `raspberry_pi_7` or `raspberry_pi_64`. Windows i386 is built with Go 1.10.8, everything else with Go 1.26.11.
    - `with_converter`: also convert data with ChemConverterApp to a BagIt archive, sent to `dst_bagit` with `user_bagit`/`passwort_bagit`; needs a JSON `profile`, `public_link` is the URL prefix of the raw files. The converter ships in the zip (Windows x64, Linux); a failing conversion is skipped and the raw data is still sent.
    - `host_key` (SFTP only): expected SSH host key fingerprint of the server, `SHA256:<base64>` (optionally `ssh-ed25519 255 SHA256:...` as shown by WinSCP) or MD5 `aa:bb:...`. It applies to both SFTP destinations, so with a converter both must be the same server. Required for `win_i386` + SFTP unless `insecure` is set. Otherwise empty means trust on first use: Shuttle stores the key of the first connection in `known_hosts` and refuses a changed key later.
    - `cert` (WebDAV only): PEM server certificate (`.crt`, `.pem`, `.cer`), needed for self-signed servers and the only way TLS is verified on Windows XP. It is built in as `server.crt` and shipped next to the executable (the download becomes a zip).
    - `insecure`: WARNING, disables TLS certificate **and** SSH host key verification. Any user may set it; use it only for tests. It is flagged ("Verification disabled") in the instance list and Shuttle logs a warning at start.
    - `linux_user`: the Linux user that runs the service; used in the systemd unit of the instance. Empty: the unit contains `User=CHANGE_ME` to replace by hand. Ignored for Windows architectures.
    - `built_version`: Shuttle version of the last successful build, shown next to the download button (empty: not built yet). The active `GitInstance` version may be newer; the next download then rebuilds. `last_build`, `last_update`: set by the system.

    Warnings shown in the instance list: "Verification disabled" (`insecure`) and "No host key" (SFTP without `host_key`: trust on first use).

    Download and installation:
    - Downloading compiles the executable from the active `GitInstance` (slow on first download or after changes); deleting also removes the build files.
    - The download is the bare executable, or a zip when a certificate (WebDAV), a converter, or Windows XP + SFTP (with WinSCP) applies. Every zip contains `INSTALL.txt` with the install steps for the instance: install folder `C:\\Program Files\\Shuttle` (Windows, plus `shuttle_task.vbs` in `shell:startup`) or `/opt/Shuttle` (Linux), working folder and log (`shuttle_log.txt`), the sent register (`sent_register.json`; the first start sends every stable file in `src` once) and `known_hosts`. `INSTALL.txt` contains no secrets.
    - Linux: the instance list has a "systemd unit" button (per-instance `shuttle.service`, owner/staff only); install it as `/etc/systemd/system/shuttle.service`, then `systemctl daemon-reload` and `systemctl enable --now shuttle.service`. A generic unit without user exists for old links.
    - Listed in `<shuttle-instance-list>`, created/edited/copied in `<shuttle-instance-edit>`.
    """
    edit_form = "main_app.forms.ShuttleInstanceForm"
    create_form = "main_app.forms.ShuttleInstanceForm"
    html_list_template = "main_app/models/ShuttleInstance/ShuttleInstance_list.html"
    html_detail_template = "main_app/models/ShuttleInstance/ShuttleInstance_details.html"

    name = models.CharField(help_text=_('Unique name of the Shuttle instance. This name cannot be changed!'),
                            max_length=50,
                            unique=True)
    user = models.CharField(help_text=_("WebDAV or SFTP user"), max_length=50, default="")
    password = models.CharField(help_text=_("WebDAV or SFTP password"), max_length=100)
    transfer = models.CharField(_('Transfer protocol'),
                                help_text=_("Upload with the WebDAV protocol (HTTP/HTTPS) or the SFTP protocol (SSH)."),
                                max_length=255, choices=TRANSFER_CHOISES, default=TRANSFER_CHOISES[0][0])
    src = models.CharField(help_text=_(
        "Source directory to monitor on the lab PC (absolute path). Enter it as it is, a backslash does not have to be doubled."),
        max_length=255)
    dst = models.CharField(help_text=_("""WebDAV or SFTP destination URL. Accepted: SFTP <code>host[:port]/path</code>, also <code>ssh://</code> or <code>sftp://</code> (port 22 by default); WebDAV <code>https://...</code> or <code>http://...</code>. If the destination is on the lsdf, the URL should be as follows:<br>
        <span style="margin-left: 20px; font-weight: 800;">SFTP</span>: os-login.lsdf.kit.edu/[OE]/[inst]/projects/[PROJECT_PATH]/<br>
        <span style="margin-left: 20px; font-weight: 800;">WebDAV</span>: https://os-webdav.lsdf.kit.edu/[OE]/[inst]/projects/[PROJECT_PATH]/<br>

                    <span style="margin-left: 30px;">[OE]-Organisationseinheit, z.B. kit.</span><br>
                    <span style="margin-left: 30px;">[inst]-Institut-Name, z.B. ioc, scc, ikp, imk-asf etc.</span><br>
                    <span style="margin-left: 30px;">[USERNAME]-User-Name z.B. xy1234, bs_abcd etc.</span><br>
                    <span style="margin-left: 30px;">[PROJECT_PATH]-Path (directory) within the LSDF</span>"""),
                           max_length=255)
    shuttle_type = models.CharField(_('Type'), help_text=_(
        "Type must be 'file', 'folder', 'tar', 'zip' or 'flat_tar'. The 'file' option means that each file is handled individually, the 'folder' option means that entire folders are transmitted only when all files in them are ready. The options 'tar' and 'zip' send a folder as a .tar.gz or zip archive, only when all files in a folder are ready. The 'flat_tar' option groups files by the common name regex and sends each group as a .tar.gz archive. If a folder changes, it is sent again completely. On the first start every stable file already in the source folder is sent once."),
                                    max_length=255, choices=TYPE_CHOISES)
    common_name_parts = models.CharField(_('Common name regex'), blank=True, max_length=255, default="^[A-Za-z]{1,4}",
                                         help_text=_(
                                             "The regex for the common name is used to collect all files that belong to the same data set. This value is only used if the type is flat tar. All files that either have the same regex group resolutions or (if you do not use groups) have the same global result are archived together<this.render_help></this.render_help>"))
    duration = models.PositiveIntegerField(
        help_text=_("Duration in seconds: how long a file (for folder types: every file of the folder) must stay unchanged before it is sent. Must be at least 1 (default 300 sec.). Failed uploads are retried with increasing waits of up to this duration."),
        default=300, validators=[MinValueValidator(1)])
    host_key = models.CharField(_('SSH host key'), max_length=255, blank=True, default='',
                                help_text=_("SFTP only: SSH host key fingerprint of the server; Shuttle then only connects to a server presenting this key. If empty, the key of the first connection is trusted and stored in known_hosts (a changed key is refused later). Formats: SHA256:<base64> (optionally preceded by the algorithm and bits, e.g. ssh-ed25519 255 SHA256:...) or MD5 aa:bb:...:ff. Get it in WinSCP (Session, Server/Protocol Information) or with: ssh-keyscan -p <port> <host> | ssh-keygen -lf - . Required for Windows XP (Windows i386) with SFTP (not tested on real hardware yet). Applies to both SFTP destinations."))
    cert = models.FileField(_('Server certificate'), upload_to='certs/', null=True, blank=True,
                            validators=[FileExtensionValidator(allowed_extensions=['crt', 'pem', 'cer'])],
                            help_text=_("WebDAV only: PEM certificate of the server (.crt, .pem or .cer), needed for self-signed servers. On Windows XP it is the only way TLS is verified. It is shipped as server.crt next to the executable (the download becomes a zip); keep it there."))
    insecure = models.BooleanField(_('Disable verification (insecure)'), default=False,
                                   help_text=_("WARNING: disables the TLS certificate AND the SSH host key verification, so the connection can be intercepted. Only for tests; Shuttle logs a warning at every start."))
    architecture = models.CharField(_('System architecture'),
                                    help_text=_(
                                        "Architecture and operating system of the lab PC where Shuttle runs: Windows i386 (incl. Windows XP), Windows 64 bit, Ubuntu 64 bit or Raspberry Pi (ARMv6, ARMv7, ARM 64 bit)."),
                                    max_length=255, choices=SYSTEM_CHOISES, default=SYSTEM_CHOISES[0][0])

    with_converter = models.BooleanField(_('With converter'), default=False, help_text=_(
        "Check to also convert the files with ChemConverterApp (needs the JSON profile). The destination above receives the raw data, the additional destination below receives the converted BagIt archive (for Chemotion). The converter is shipped in the downloaded zip (Windows x64 and Linux) and must stay next to the executable; if a conversion fails, it is skipped and the raw data is still sent."))

    user_bagit = models.CharField(help_text=_("WebDAV or SFTP user for the converted BagIt archive"), max_length=50, null=True,
                                  blank=True)
    passwort_bagit = models.CharField(help_text=_("WebDAV or SFTP password for the converted BagIt archive"), max_length=100,
                                      null=True, blank=True)
    dst_bagit = models.CharField(help_text=_("""WebDAV or SFTP destination URL. Accepted: SFTP <code>host[:port]/path</code>, also <code>ssh://</code> or <code>sftp://</code> (port 22 by default); WebDAV <code>https://...</code> or <code>http://...</code>. If the destination is on the lsdf, the URL should be as follows:<br>
            <span style="margin-left: 20px; font-weight: 800;">SFTP</span>: os-login.lsdf.kit.edu/[OE]/[inst]/projects/[PROJECT_PATH]/<br>
            <span style="margin-left: 20px; font-weight: 800;">WebDAV</span>: https://os-webdav.lsdf.kit.edu/[OE]/[inst]/projects/[PROJECT_PATH]/<br>

                        <span style="margin-left: 30px;">[OE]-Organisationseinheit, z.B. kit.</span><br>
                        <span style="margin-left: 30px;">[inst]-Institut-Name, z.B. ioc, scc, ikp, imk-asf etc.</span><br>
                        <span style="margin-left: 30px;">[USERNAME]-User-Name z.B. xy1234, bs_abcd etc.</span><br>
                        <span style="margin-left: 30px;">[PROJECT_PATH]-Path (directory) within the LSDF</span>"""),
                                 max_length=255, null=True, blank=True)
    public_link = models.URLField(blank=True, null=True, help_text=_("The prefix of the publicly accessible link to the raw files. It must include the scheme, domain, and path (e.g. https://your-file-storage-example.eu/data/raw/). Only the file name is appended."))
    profile = models.FileField(upload_to="profiles/", validators=[FileExtensionValidator(allowed_extensions=["json"])],
                               null=True, blank=True)

    last_update = models.DateTimeField(default=timezone.now)
    last_build = models.DateTimeField(null=True, blank=True)
    linux_user = models.CharField(_('Linux user'), max_length=32, blank=True, default='',
                                  help_text=_('The Linux user that runs the systemd service; its home holds the working folder (~/shuttle). It is written into the unit file of the instance. Leave empty to replace User=CHANGE_ME in the unit file by hand.'))
    built_version = models.CharField(_('Built Shuttle version'), max_length=20, blank=True, default='',
                                     help_text=_('Shuttle version of the last successful build (empty: not built yet). The active git repository may be newer; the next download then rebuilds.'))
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        if not self.owner:
            self.owner = self.scope['user']
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        build_path = self.get_path()
        shutil.rmtree(build_path, ignore_errors=True)
        try:
            os.remove(build_path.rstrip('/') + '.lock')
        except OSError:
            pass
        super().delete(using, keep_parents)

    def get_path(self):
        file_paths = os.path.join('./projects/builds/', self.name)
        os.makedirs(file_paths, exist_ok=True)
        return file_paths

    def _get_build_config(self):
        return make_context({"src": go_str(self.src),
                             "dst": go_str(self.dst),
                             "user": go_str(self.user),
                             "password": go_str(self.password),
                             "duration": go_str(self.duration),
                             "common_regex": go_str(self.common_name_parts),
                             "tType": go_str(self.transfer),
                             "name": go_str(self.name),
                             "crt": "server.crt" if self._cert_applies() else "",
                             "hostkey": go_str(self.host_key.strip()) if self.transfer == 'sftp' else "",
                             "insecure": "1" if self.insecure else "",
                             "type": go_str(self.shuttle_type),
                             "preconvert": "T" if self.with_converter else "N",
                             "dst_converter": go_str(self.dst_bagit),
                             "user_converter": go_str(self.user_bagit),
                             "password_converter": go_str(self.passwort_bagit),
                             "public": go_str(self.public_link)})

    def _cert_applies(self):
        """A certificate is bundled (as `server.crt`) only for WebDAV."""
        return bool(self.cert) and self.transfer == 'webdav'

    def only_exe(self):
        if self._cert_applies():
            return False
        if self.architecture == 'win_i386' and self.transfer == 'sftp':
            return False
        return not self.with_converter

    def build(self):
        filename = 'shuttle.exe' if self.architecture.startswith('win') else 'shuttle'
        tp = self.get_path()
        tp_bin = os.path.abspath(os.path.join(tp, 'bin'))
        target = os.path.join(tp_bin, filename)
        builds_dir = os.path.dirname(os.path.abspath(tp))
        git_lock = os.path.join(os.path.abspath('./projects/git_repos'), '.lock')

        with file_lock(os.path.abspath(tp) + '.lock'):
            git = GitInstance.objects.get(is_active=True)
            if git.last_reload is None:
                git.git_reload()
            if self.pk:
                # another request may have built while we waited for the lock
                self.last_build = ShuttleInstance.objects.filter(pk=self.pk).values_list(
                    'last_build', flat=True).first()
            if not (self.last_build is None or self.last_build <= git.last_reload
                    or self.last_update > self.last_build or not os.path.exists(target)):
                return target

            __, repo_path = git.get_path()
            with file_lock(git_lock, shared=True):
                built, tmp_root = compile_into_temp(self, repo_path, builds_dir, filename, self._get_build_config())
            try:
                os.makedirs(tp_bin, exist_ok=True)
                os.replace(built, target)
            finally:
                shutil.rmtree(tmp_root, ignore_errors=True)
            self.last_build = timezone.now()
            self.built_version = git.shuttle_version
            if self.pk:
                # update() instead of save(): save() would bump last_update and force a rebuild next time
                ShuttleInstance.objects.filter(pk=self.pk).update(last_build=self.last_build,
                                                                  built_version=self.built_version)
        return target

    @classmethod
    def render(cls, template_name, context=None, request=None, using=None):
        if template_name == getattr(cls.SdcMeta, 'html_list_template'):
            sf = ShuttleInstanceSearchForm(data=context.get("filter", {}))
            context = context | handle_search_form(context["instances"], sf, range=10)
        return render_to_string(template_name=template_name, context=context, request=request, using=using)

    @classmethod
    def is_authorised(cls, user, action, obj):
        return user.is_authenticated

    @classmethod
    def get_queryset(cls, user, action, obj):
        if user.is_superuser or user.is_staff:
            return cls.objects.all()
        return cls.objects.filter(owner=user)
