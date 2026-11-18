import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.utils.encoding import smart_str
import datetime


# Create your views here.


class DownloadVbs(View):

    filename = 'shuttle_task.vbs'
    file_content = b'''Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.CurrentDirectory = "C:\\Program Files\\Shuttle"
WinScriptHost.Run Chr(34) & "C:\\Program Files\\Shuttle\\shuttle.exe" & Chr(34), 0
Set WinScriptHost = Nothing
'''


    def get(self, request):

        response = HttpResponse(self.file_content)
        response['X-SendFile'] = request.build_absolute_uri()
        response['Content-Type'] = 'Text/vbscript'
        response['Content-Length'] = len(self.file_content)
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(self.filename)
        response['Last-Modified'] = datetime.datetime.now()

        return response


UNIT_TEMPLATE = """[Unit]
Description={description}
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
# {user_comment}
User={user}
WorkingDirectory=/opt/Shuttle
ExecStart=/opt/Shuttle/shuttle
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

LINUX_USER_RE = re.compile(r'^[a-z_][a-z0-9_-]{0,31}$')
CONTROL_RE = re.compile(r'[\x00-\x1f\x7f-\x9f\u2028\u2029]')


def render_unit(description, user=''):
    """Systemd unit text. Only the sanitized description and a validated user are written."""
    description = CONTROL_RE.sub('', description or '').strip()
    if user and LINUX_USER_RE.match(user):
        comment = 'The user whose home holds the Shuttle working folder (~/shuttle/shuttle_<name>/).'
    else:
        user = 'CHANGE_ME'
        comment = ('The user whose home holds the Shuttle working folder (~/shuttle/shuttle_<name>/). '
                   'Replace CHANGE_ME with the Linux user.')
    return UNIT_TEMPLATE.format(description=description, user=user, user_comment=comment).encode('utf-8')


def unit_response(request, content, filename):
    response = HttpResponse(content)
    response['X-SendFile'] = request.build_absolute_uri()
    response['Content-Type'] = 'Text/*'
    response['Content-Length'] = len(content)
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(filename)
    response['Last-Modified'] = datetime.datetime.now()
    return response


class DownloadService(View):
    """Generic unit, kept for old links."""

    filename = 'shuttle.service'

    def get(self, request):
        return unit_response(request, render_unit('Shuttle'), self.filename)


class DownloadInstanceService(LoginRequiredMixin, View):
    """Systemd unit of one Linux instance (owner, staff or superuser only)."""

    raise_exception = True
    filename = 'shuttle.service'

    def get(self, request, pk):
        from main_app.models import ShuttleInstance
        instance = get_object_or_404(ShuttleInstance, pk=pk)
        user = request.user
        if not (user.is_staff or user.is_superuser or instance.owner_id == user.pk):
            raise Http404()
        if not instance.architecture or instance.architecture.startswith('win'):
            raise Http404()
        return unit_response(request, render_unit('Shuttle (%s)' % instance.name, instance.linux_user), self.filename)
