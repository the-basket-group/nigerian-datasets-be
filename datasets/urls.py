from django.urls import path

from datasets.views import (
    DeleteDatasetFileView,
    DeleteDatasetVersionView,
    DeleteDatasetView,
    RetrieveDatasetView,
    SearchDatasetView,
    UpdateDatasetVersion,
    UpdateDatasetView,
    UploadDatasetView,
)

urlpatterns = [
    path("", UploadDatasetView.as_view(), name="upload_dataset"),
    path("internal/search/", SearchDatasetView.as_view(), name="list_datasets"),
    path("<str:id>/update/", UpdateDatasetView.as_view(), name="update_dataset"),
    path("<str:id>/view/", RetrieveDatasetView.as_view(), name="retrieve_dataset"),
    path(
        "<str:id>/versions/update/",
        UpdateDatasetVersion.as_view(),
        name="update_dataset_version",
    ),
    path(
        "<str:id>/delete/",
        DeleteDatasetView.as_view(),
        name="delete_dataset",
    ),
    path(
        "versions/<str:id>/delete/",
        DeleteDatasetVersionView.as_view(),
        name="delete_dataset_version",
    ),
    path(
        "files/<str:id>/delete/",
        DeleteDatasetFileView.as_view(),
        name="delete_dataset_file",
    ),
]
