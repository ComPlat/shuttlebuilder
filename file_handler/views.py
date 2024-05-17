from django.http import HttpResponse
from django.views import View
from django.utils.encoding import smart_str
import datetime


# Create your views here.


class DownloadVbs(View):

    filename = 'shuttle_task.vbs'
    file_content = b'''Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "C:\\Program Files\\file_exporter\\shuttle.exe" & Chr(34), 0
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


class DownloadService(View):

    filename = 'shuttle.service'
    file_content = b'''[Unit]
Description=EFW (ELN file exporter) service
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=!!!!
ExecStart=/opt/file_exporter/shuttle

[Install]
WantedBy=multi-user.target
'''


    def get(self, request):

        response = HttpResponse(self.file_content)
        response['X-SendFile'] = request.build_absolute_uri()
        response['Content-Type'] = 'Text/*'
        response['Content-Length'] = len(self.file_content)
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(self.filename)
        response['Last-Modified'] = datetime.datetime.now()

        return response
