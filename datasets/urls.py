from django.urls import path

from datasets.views import ListDatasetView, UploadDatasetView

urlpatterns = [
    path("", UploadDatasetView.as_view(), name="upload_dataset"),
    path("list/", ListDatasetView.as_view(), name="list_datasets"),
]
