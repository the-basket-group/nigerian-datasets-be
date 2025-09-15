import os
from typing import Any

from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from datasets.models import Dataset, DatasetFile, DatasetVersion, Tag
from datasets.serializers import CreateDatasetSerializer, DatasetSerializer
from datasets.utils import (
    compute_completeness,
    compute_metadata,
    upload_datasetfile_to_gcloud,
)
from users.models import User
from users.permissions import is_accessible

PageNumberPagination.page_size = 20


class UploadDatasetView(CreateAPIView):
    permission_classes = [is_accessible("admin", "member")]
    parser_classes = [MultiPartParser]
    serializer_class = CreateDatasetSerializer

    def create(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        owner: User = User.objects.get(id=str(request.user.id))
        is_approved = (
            True
            if owner.role == "admin"
            and serializer.validated_data["status"] == "published"
            else False
        )
        approved_by: User | None = (
            owner
            if owner.role == "admin"
            and serializer.validated_data["status"] == "published"
            else None
        )

        dataset = Dataset.objects.create(
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            license=serializer.validated_data.get("license", ""),
            source_org=serializer.validated_data.get("source_org", ""),
            geography=serializer.validated_data.get("geography", "Nigeria"),
            update_frequency=serializer.validated_data.get("update_frequency", "never"),
            is_public=serializer.validated_data.get("is_public"),
            metadata=serializer.validated_data.get("metadata", {}),
            status=serializer.validated_data.get("status", "draft"),
            owner=owner,
            is_approved=is_approved,
            approved_by=approved_by,
        )

        # Dataset tags added
        tags_data = serializer.validated_data.get("tags", [])
        tag_list = []
        for tag_name in tags_data:
            tags, _ = Tag.objects.get_or_create(name=tag_name.strip().lower())
            tag_list.append(tags)

        dataset.tags.set(tag_list)

        dataset_version = DatasetVersion.objects.create(
            dataset=dataset,
            version_label=serializer.validated_data.get("version_label", "v1.0.0"),
            metadata={},
            changelog=[],
            owner=owner,
        )

        for file in request.FILES.getlist("files"):
            file.seek(0)
            file_info = upload_datasetfile_to_gcloud(file)
            _, ext = os.path.splitext(file.name)
            ext = ext.replace(".", "")
            metadata: dict[Any, Any] | None = compute_metadata(file)
            if metadata is None:
                metadata = {}

            DatasetFile.objects.create(
                dataset_version=dataset_version,
                upload_id=file_info.id,
                upload_url=file_info.public_url or "",
                file_format=ext,
                file_size_bytes=file_info.size,
                checksum=file_info.md5_hash,
                owner=owner,
                metadata={
                    "file_info": metadata.get("file_info"),
                    "structure": metadata.get("structure"),
                    "extraction_timestamp": metadata.get("extraction_timestamp"),
                    "failure_reason": metadata.get("failure_reason"),
                    "meta_generation_failure": metadata.get(
                        "meta_generation_failure", False
                    ),
                    "meta_generation_failure_timestamp": metadata.get(
                        "meta_generation_failure_timestamp"
                    ),
                },
                column_schema=metadata.get("column_schema", []),
            )

        dataset.completeness_score = compute_completeness(dataset)
        dataset.save()

        response_data = DatasetSerializer(instance=dataset)
        return Response(
            data={"success": True, "dataset": response_data.data}, status=201
        )


class ListDatasetView(ListAPIView):
    serializer_class = DatasetSerializer
    # TODO: search, filter and sort implementations
    # TODO: user-level Dataset viewing
    queryset = Dataset.objects.all()
    pagination_class = PageNumberPagination
