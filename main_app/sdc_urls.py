from django.urls import path, re_path
from . import sdc_views

# Do not add an app_name to this file

urlpatterns = [
    # scd view below
    path('shuttle_instance_edit', sdc_views.ShuttleInstanceEdit.as_view(), name='scd_view_shuttle_instance_edit'),
    path('shuttle_instance_list', sdc_views.ShuttleInstanceList.as_view(), name='scd_view_shuttle_instance_list'),
    path('git_insatnce_edit', sdc_views.GitInsatnceEdit.as_view(), name='scd_view_git_insatnce_edit'),
    path('git_instance_list', sdc_views.GitInstanceList.as_view(), name='scd_view_git_instance_list'),
    path('basic_info', sdc_views.BasicInfo.as_view(), name='scd_view_basic_info'),

    path('shuttle_download/<int:pk>', sdc_views.ShuttleDownload.as_view(), name='scd_view_shuttle_download'),
]
