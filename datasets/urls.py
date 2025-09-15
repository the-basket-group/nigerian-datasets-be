from django.urls import path

from datasets.views import (
    ListDatasetView,
    RetrieveDatasetView,
    UpdateDatasetVersion,
    UpdateDatasetView,
    UploadDatasetView,
)

urlpatterns = [
    path("", UploadDatasetView.as_view(), name="upload_dataset"),
    path("list/", ListDatasetView.as_view(), name="list_datasets"),
    path("<str:id>/update/", UpdateDatasetView.as_view(), name="update_dataset"),
    path("<str:id>/view/", RetrieveDatasetView.as_view(), name="retrieve_dataset"),
    path(
        "<str:id>/versions/update/",
        UpdateDatasetVersion.as_view(),
        name="update_dataset_version",
    ),
]
