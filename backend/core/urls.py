from django.urls import path

from core.views import *

app_name = "core"


urlpatterns = [

    path(
        "upload/",
        UploadAPIView.as_view(),
        name="upload",
    ),

    path(
        "dashboard/",
        DashboardAPIView.as_view(),
        name="dashboard",
    ),
]