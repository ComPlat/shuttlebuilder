from django.urls import path, re_path
from . import views

# Do not add an app_name to this file

urlpatterns = [
    # scd view below
    path('download/file_exporter_task.vbs', views.DownloadVbs.as_view(), name='shuttle_task.vbs'),
    path('download/shuttle.service', views.DownloadService.as_view(), name='file_shuttle.service'),

]
