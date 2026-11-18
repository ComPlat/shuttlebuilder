import logging
import os
import uuid
import tempfile
import zipfile

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from sdc_core.sdc_extentions.views import SDCView, SdcLoginRequiredMixin
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.html import escape
from django.utils.translation import gettext as _

from main_app.build import BuildError
from main_app.models import GitInstance, ShuttleInstance, ElnConnection

logger = logging.getLogger("main_app.build")


class BasicInfo(SDCView):
    template_name='main_app/sdc/basic_info.html'

    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class GitInstanceList(SdcLoginRequiredMixin, SDCView):
    template_name='main_app/sdc/git_instance_list.html'

    def activate_git(self, request, *args, **kwargs):
        gi = GitInstance.objects.get(pk=kwargs.get('pk'))
        gi.git_reload()
        gi.set_active()

    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class GitInsatnceEdit(SdcLoginRequiredMixin, SDCView):
    template_name='main_app/sdc/git_insatnce_edit.html'


    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class ShuttleInstanceList(SdcLoginRequiredMixin, SDCView):
    template_name='main_app/sdc/shuttle_instance_list.html'

    def get_content(self, request, *args, **kwargs):
        gitInstance = GitInstance.get_active()
        return render(request, self.template_name, {'gitInstance': gitInstance})

class ShuttleInstanceEdit(SdcLoginRequiredMixin, SDCView):
    template_name='main_app/sdc/shuttle_instance_edit.html'

    def get_content(self, request, *args, **kwargs):
        gitInstance = GitInstance.get_active()
        return render(request, self.template_name, {'gitInstance': gitInstance})


class ShuttleDownload(SdcLoginRequiredMixin, SDCView):
    raise_exception = True

    @staticmethod
    def _error_response(message, reference, detail):
        body = '<h1>%s</h1>' % escape(message)
        if reference:
            body += '<p>%s %s</p>' % (escape(_('Reference:')), escape(reference))
        if detail:
            body += '<pre>%s</pre>' % escape(detail)
        return HttpResponseServerError(body)

    @staticmethod
    def _zip_name(instance):
        if instance.architecture == 'win_i386' and instance.transfer == 'sftp':
            return 'shuttle_sftp_winxp.zip'
        if instance.with_converter:
            return 'shuttle_with_converter.zip'
        return 'shuttle_%s.zip' % instance.architecture

    @staticmethod
    def _cert_bytes(instance):
        """Bytes of the server certificate if it applies (WebDAV only), else None."""
        if not instance.cert or instance.transfer != 'webdav':
            return None
        instance.cert.open('rb')
        try:
            return instance.cert.read()
        finally:
            instance.cert.close()

    def _zip_response(self, instance, file_location, zip_name):
        """Pack the executable with everything that has to ship next to it into a temporary zip."""
        static_files = os.path.join(settings.STATIC_ROOT, 'files')
        cert = self._cert_bytes(instance)
        tmp = tempfile.NamedTemporaryFile(prefix='shuttle_', suffix='.zip', delete=False,
                                          dir=os.path.dirname(file_location))
        tmp.close()
        try:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                if zip_name == 'shuttle_sftp_winxp.zip':
                    zf.write(file_location, 'shuttle.exe')
                    zf.write(os.path.join(static_files, 'license.txt'), 'license.txt')
                    zf.write(os.path.join(static_files, 'WinSCP.com'), 'WinSCP.com')
                    zf.write(os.path.join(static_files, 'WinSCP.exe'), 'WinSCP.exe')
                else:
                    zf.write(file_location, os.path.basename(file_location))
                    if instance.with_converter:
                        if instance.architecture == 'win_64':
                            zf.write(os.path.join(static_files, 'ChemConverterApp.exe'), 'ChemConverterApp.exe')
                        else:
                            zf.write(os.path.join(static_files, 'ChemConverterApp'), 'ChemConverterApp')
                        instance.profile.open('r')
                        zf.writestr(instance.profile.name, instance.profile.read())
                        instance.profile.close()
                if cert is not None:
                    zf.writestr('server.crt', cert)
            with open(tmp.name, 'rb') as f:
                file_data = f.read()
        finally:
            try:
                os.remove(tmp.name)
            except OSError:
                pass
        response = HttpResponse(file_data, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename="%s"' % zip_name
        return response

    def get(self, request, pk, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            filter_set = dict(pk=pk)
        else:
            filter_set = dict(pk=pk, owner=request.user)

        instance = get_object_or_404(ShuttleInstance, **filter_set)
        is_staff = request.user.is_staff or request.user.is_superuser
        try:
            file_location = instance.build()
            if instance.only_exe():
                with open(file_location, 'rb') as f:
                    file_data = f.read()
                    response = HttpResponse(file_data, content_type='application/octet-stream')
                    response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_location)
            else:
                zip_name = self._zip_name(instance)
                response = self._zip_response(instance, file_location, zip_name)

        except BuildError as e:
            response = self._error_response(e.public_message, e.reference, e.detail if is_staff else "")
        except IOError:
            # handle file not exist case here
            response = HttpResponseNotFound('<h1>%s</h1>' % escape(_('File not found')))
        except Exception:
            reference = uuid.uuid4().hex[:8]
            logger.exception("Download of Shuttle instance %s failed unexpectedly (reference %s)",
                             instance.name, reference)
            response = self._error_response(_("Building the Shuttle failed."), reference, "")

        return response

class ShuttleScripts(SdcLoginRequiredMixin, SDCView):
    template_name='main_app/sdc/shuttle_scripts.html'

    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name)

class ShuttleLogin(SDCView):
    template_name='main_app/sdc/shuttle_login.html'

    def get_content(self, request, *args, **kwargs):
        return render(request, self.template_name, {'connection': ElnConnection.get_active()})