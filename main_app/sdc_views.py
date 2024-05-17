import os
import zipfile

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from sdc_core.sdc_extentions.views import SDCView, SdcGroupRequiredMixin
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from main_app.models import GitInstance, ShuttleInstance


class BasicInfo(SDCView):
    template_name='main_app/sdc/basic_info.html'

    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class GitInstanceList(SdcGroupRequiredMixin, SDCView):
    template_name='main_app/sdc/git_instance_list.html'

    def activate_git(self, channel, *args, **kwargs):
        user = channel.scope.get('user')
        gi = GitInstance.objects.get(pk=kwargs.get('pk'))
        gi.git_reload()
        gi.set_active()

    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class GitInsatnceEdit(SdcGroupRequiredMixin, SDCView):
    template_name='main_app/sdc/git_insatnce_edit.html'


    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class ShuttleInstanceList(SDCView):
    template_name='main_app/sdc/shuttle_instance_list.html'

    def get_content(self, request, *args, **kwargs):
        gitInstance = GitInstance.get_active()
        return render(request, self.template_name, {'gitInstance': gitInstance})

class ShuttleInstanceEdit(SDCView):
    template_name='main_app/sdc/shuttle_instance_edit.html'

    def get_content(self, request, *args, **kwargs):
        gitInstance = GitInstance.get_active()
        return render(request, self.template_name, {'gitInstance': gitInstance})


class ShuttleDownload(LoginRequiredMixin, SDCView):
    raise_exception = True

    def get(self, request, pk, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            filter_set = dict(pk=pk)
        else:
            filter_set = dict(pk=pk, owner=request.user)

        instance = ShuttleInstance.objects.get(**filter_set)
        try:
            file_location = instance.build()
            if instance.only_exe():
                with open(file_location, 'rb') as f:
                    file_data = f.read()
                    response = HttpResponse(file_data, content_type='application/octet-stream')
                    response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_location)
            else:
                zip_path = os.path.join(os.path.dirname(file_location), "shuttle_sftp_winxp.zip")
                zf = zipfile.ZipFile(zip_path, "w")
                zf.write(file_location, 'efw.exe')
                zf.write(os.path.join(settings.STATIC_ROOT, 'Utils/files/license.txt'), 'license.txt')
                zf.write(os.path.join(settings.STATIC_ROOT, 'Utils/files/WinSCP.com'), 'WinSCP.com')
                zf.write(os.path.join(settings.STATIC_ROOT, 'Utils/files/WinSCP.exe'), 'WinSCP.exe')
                zf.close()
                with open(zip_path, 'rb') as f:
                    file_data = f.read()
                    response = HttpResponse(file_data, content_type='application/octet-stream')
                    response['Content-Disposition'] = 'attachment; filename="efw_sftp_winxp.zip"'

        except IOError:
            # handle file not exist case here
            response = HttpResponseNotFound('<h1>File not exist</h1>')
        except Exception as e:
            response = HttpResponseServerError(
                '<h1>%s</h1>' % _('There was en compilation error. Maybe you have used \\ in the src instead of \\\\.'))

        return response