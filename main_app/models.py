import glob
import os
import re
import shutil
import subprocess

from django.conf import settings
from django.utils import timezone
from sdc_core.sdc_extentions.models import SdcModel
from sdc_core.sdc_extentions.forms import AbstractSearchForm
from django.template.loader import render_to_string
from sdc_core.sdc_extentions.search import handle_search_form
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import signals
from django.template import Template, Context
from distutils.dir_util import copy_tree


def create_user(sender, instance, created, **kwargs):
    """Create ElnUser for every new User."""
    if created:
        ElnUser.objects.create(user=instance)


signals.post_save.connect(create_user, sender=User, weak=False,
                          dispatch_uid='models.create_eln_user_profile')


class ElnUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, default='')
    is_eln_user = models.BooleanField(default=False)


# Create your models here.

class ElnConnectionSearchForm(AbstractSearchForm):
    CHOICES = (("url", "Url"), ("active", "Active"),)
    PLACEHOLDER = ""
    DEFAULT_CHOICES = CHOICES[0][0]
    SEARCH_FIELDS = ("url",)


class ElnConnection(models.Model, SdcModel):
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
        if template_name == cls.html_list_template:
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
        (instance, c) = ElnConnection.objects.get_or_create(active=True)
        if c:
            instance.url = settings.ELN_URL
            instance.save()
        return instance


class GitInstanceSearchForm(AbstractSearchForm):
    CHOICES = (("url", "Url"), ("branch", "Branch"),)
    PLACEHOLDER = ""
    DEFAULT_CHOICES = CHOICES[0][0]
    SEARCH_FIELDS = ("url", "branch")


class GitInstance(models.Model, SdcModel):
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
            return None
        except:
            return None

    def set_active(self):
        GitInstance.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True
        self.save()

    def git_reload(self):
        file_paths, x = self.get_path()
        shutil.rmtree(os.path.join(file_paths), ignore_errors=True)
        os.makedirs(file_paths, exist_ok=True)
        abs_path = os.path.abspath(file_paths)
        p = subprocess.Popen(['git', 'clone', self.url], cwd=abs_path)
        p_status = p.wait()
        if p_status != 0:
            raise Exception(_("Url cannot be cloned: %s") % self.url)
        x, abs_path = self.get_path()
        p = subprocess.Popen(['git', 'checkout', self.branch], cwd=abs_path)
        p_status = p.wait()
        if p_status != 0:
            raise Exception(_("Branch or ID cannot be checked out: %s") % self.branch)
        files = glob.glob(os.path.join(file_paths, '*', '.git'))
        for f in files:
            shutil.rmtree(f)
        files = glob.glob(os.path.join(file_paths, '*', 'bin'))
        for f in files:
            shutil.rmtree(f)

        self.last_reload = timezone.now()
        self.save()

    @classmethod
    def render(cls, template_name, context=None, request=None, using=None):
        if template_name == cls.html_list_template:
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
        ('name', _('Name')), ('user', _('User')), ('efw_type', _('Type')), ('src', _('Source')),
        ('dst', _('Destination')),
        ('architecture', _('Architecture')))
    PLACEHOLDER = _('Name, Type, Source, Destination')
    DEFAULT_CHOICES = CHOICES[0][0]
    SEARCH_FIELDS = ('name', 'user', 'efw_type', 'src', 'dst', 'architecture')


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
    ('ubuntu_64', _('Ubuntu 64 Bit'))
)
TRANSFER_CHOISES = (
    ('webdav', _('WebDAV')),
    ('sftp', _('SFTP')),
)


class ShuttleInstance(models.Model, SdcModel):
    edit_form = "main_app.forms.ShuttleInstanceForm"
    create_form = "main_app.forms.ShuttleInstanceForm"
    html_list_template = "main_app/models/ShuttleInstance/ShuttleInstance_list.html"
    html_detail_template = "main_app/models/ShuttleInstance/ShuttleInstance_details.html"

    name = models.CharField(help_text=_('Unique name of the Shuttle instance. This name cannot be changed!'),
                            max_length=50,
                            unique=True)
    user = models.CharField(help_text=_("WebDAV or STFP User"), max_length=50, default="")
    password = models.CharField(help_text=_("WebDAV or STFP Password"), max_length=100)
    transfer = models.CharField(_('Transfer protocol'),
                                help_text=_("You can either use the WebDAV protocol or the SFTP protocol"),
                                max_length=255, choices=TRANSFER_CHOISES, default=TRANSFER_CHOISES[0][0])
    src = models.CharField(help_text=_(
        "Source directory to monitor. Note: If you use only single \\ in the path, the build will fail. Therefore, make sure that you always use \\\\."),
        max_length=255)
    dst = models.CharField(help_text=_("""WebDAV or SFTP destination URL. If the destination is on the lsdf, the URL should be as follows:<br>
        <span style="margin-left: 20px; font-weight: 800;">SFTP</span>: os-login.lsdf.kit.edu/[OE]/[inst]/projects/[PROJECT_PATH]/<br>
        <span style="margin-left: 20px; font-weight: 800;">WebDAV</span>: https://os-webdav.lsdf.kit.edu/[OE]/[inst]/projects/[PROJECT_PATH]/<br>

                    <span style="margin-left: 30px;">[OE]-Organisationseinheit, z.B. kit.</span><br>
                    <span style="margin-left: 30px;">[inst]-Institut-Name, z.B. ioc, scc, ikp, imk-asf etc.</span><br>
                    <span style="margin-left: 30px;">[USERNAME]-User-Name z.B. xy1234, bs_abcd etc.</span><br>
                    <span style="margin-left: 30px;">[PROJECT_PATH]-Path (directory) within the LSDF</span>"""),
                           max_length=255)
    shuttle_type = models.CharField(_('Type'), help_text=_(
        "Type must be 'file', 'folder', 'tar' or 'zip'. The 'file' option means that each file is handled individually, the 'folder' option means that entire folders are transmitted only when all files in them are ready. The options 'tar' ond/or 'zip' sends a folder zipped (or compressed as tar archieve), only when all files in a folder are ready."),
                                    max_length=255, choices=TYPE_CHOISES)
    common_prefix = models.PositiveIntegerField(_('Common prefix length'), default=0, help_text=_(
        "The common prefix length is only required if the type is flat_tar. This value specifies the number of leading characters that must be the same in order for files to be packed together."))
    duration = models.PositiveIntegerField(
        help_text=_("Duration in seconds, i.e., how long a file must not be changed before sent. (default 300 sec.)"),
        default=300)
    # cert = models.CharField(help_text=_("Path to server TLS certificate. Only needed if the server has a self signed certificate."), max_length=255, blank=True, null=True)
    architecture = models.CharField(_('System architecture'),
                                    help_text=_("Your computer architecture : either 64 bit or 32 bit (i386) "),
                                    max_length=255, choices=SYSTEM_CHOISES, default=SYSTEM_CHOISES[0][0])

    last_update = models.DateTimeField(default=timezone.now)
    last_build = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        build_path = self.get_path()
        shutil.rmtree(build_path)
        super().delete(using, keep_parents)

    def get_path(self):
        file_paths = os.path.join('./projects/builds/', self.name)
        os.makedirs(file_paths, exist_ok=True)
        return file_paths

    def _get_build_config(self):
        return Context({"src": self.src,
                        "dst": self.dst,
                        "user": self.user,
                        "password": self.password,
                        "duration": self.duration,
                        "cpf": self.common_prefix,
                        "tType": self.transfer,
                        "name": self.name,
                        "crt": "None",
                        "type": self.shuttle_type})

    def only_exe(self):
        return self.architecture != 'win_i386' or self.transfer != 'sftp'

    def build(self):
        git = GitInstance.objects.get(is_active=True)
        if git.last_reload is None:
            git.git_reload()
        __, repo_path = git.get_path()

        tp = self.get_path()
        tp_bin = os.path.abspath(os.path.join(tp, 'bin'))
        tp_src = os.path.abspath(os.path.join(tp, 'src'))

        if self.architecture != 'ubuntu_64':
            filename = 'shuttle.exe'
        else:
            filename = 'shuttle'

        if self.last_build is None or self.last_build <= git.last_reload or self.last_update > self.last_build:
            shutil.rmtree(tp, ignore_errors=True)
            os.makedirs(tp_src, exist_ok=True)
            copy_tree(repo_path, tp_src)

            for root, dirs, files in os.walk(tp_src, topdown=False):
                for name in files:
                    f = open(os.path.join(root, name), "r")
                    try:
                        text = f.read()
                        t = Template(text)
                        f.close()
                        text = t.render(self._get_build_config())
                        f = open(os.path.join(root, name), "w")
                        f.write(text)
                        f.close()
                    except:
                        raise Exception(_("Compiling failed"))
            os.makedirs(tp_bin, exist_ok=True)
            my_env = os.environ.copy()
            my_env["GOROOT"] = settings.GOROOT
            my_env["GOPATH"] = settings.GOPATH
            if self.architecture != 'ubuntu_64':
                my_env["GOOS"] = settings.GOOS

            if self.architecture == 'win_i386':
                my_env['GOARCH'] = '386'
                go_tool = "go1.10"
            else:
                go_tool = os.path.join(settings.GOROOT, "bin/go")
                p = subprocess.Popen([go_tool, "mod", "download"], env=my_env, cwd=tp_src)
                p_status = p.wait()
                print(p, p_status)
                if p_status != 0:
                    raise Exception(_("Download mod failed"))

            p = subprocess.Popen(
                [go_tool, "build", "-o", os.path.join(tp_bin, filename)], env=my_env,
                cwd=tp_src)
            p_status = p.wait()
            print(p, p_status)
            if p_status != 0:
                raise Exception(_("Compiling failed"))

            shutil.rmtree(tp_src, ignore_errors=True)
            self.last_build = timezone.now()
            self.save()
        return os.path.join(tp_bin, filename)

    @classmethod
    def render(cls, template_name, context=None, request=None, using=None):
        if template_name == cls.html_list_template:
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
