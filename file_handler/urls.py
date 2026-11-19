from django.urls import path, re_path
from . import views

# Do not add an app_name to this file

urlpatterns = [
    # scd view below
    path('download/shuttle_task.vbs', views.DownloadVbs.as_view(), name='shuttle_task.vbs'),
    # old URL, kept for existing links and bookmarks
    path('download/file_exporter_task.vbs', views.DownloadVbs.as_view(), name='shuttle_task_legacy.vbs'),
    path('download/shuttle.service', views.DownloadService.as_view(), name='file_shuttle.service'),
    path('download/<int:pk>/shuttle.service', views.DownloadInstanceService.as_view(), name='file_shuttle_instance.service'),

]
