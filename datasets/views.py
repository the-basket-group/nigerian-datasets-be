import hashlib
import os
from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from datasets.models import Dataset, DatasetFile, DatasetVersion, Tag
from datasets.serializers import (
    CreateDatasetSerializer,
    DatasetSearchSerializer,
    DatasetSerializer,
    DatasetVersionSerializer,
    UpdateDatasetSerializer,
    UpdateDatasetVersionSerializer,
)
from datasets.utils import (
    compute_completeness,
    compute_metadata,
    delete_dataset_task,
    delete_file_task,
    delete_version_task,
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
            is_public=serializer.validated_data.get("is_public", False),
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
            version_label="v1",
            version_number=1,
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

            file.seek(0)
            md5_hash = hashlib.md5(file.read()).hexdigest()
            DatasetFile.objects.create(
                dataset_version=dataset_version,
                upload_id=file_info.id,
                upload_url=file_info.public_url or "",
                file_format=ext,
                file_size_bytes=file_info.size,
                checksum=md5_hash,
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
                dataset=dataset,
            )

        dataset.completeness_score = compute_completeness(dataset)
        dataset.save()

        response_data = DatasetSerializer(instance=dataset)
        return Response(
            data={"success": True, "dataset": response_data.data}, status=201
        )


class SearchDatasetView(APIView):
    # TODO: user-level Dataset viewing
    queryset = Dataset.objects.all()
    pagination_class = PageNumberPagination

    def post(self, request: Request) -> Response:
        serializer = DatasetSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # form the query builder of kwargs
        base_query = Q(is_public=True)

        if request.user.is_authenticated:
            base_query = base_query | Q(owner=request.user)

        secondary_query = Q()
        filters = serializer.validated_data
        if "search" in filters:
            secondary_query = Q(title__icontains=filters["search"]) | Q(
                description__icontains=filters["search"]
            )

        if "file_types" in filters:
            secondary_query = secondary_query & Q(
                files__file_format__in=filters["file_types"]
            )

        if "licenses" in filters:
            secondary_query = secondary_query & Q(license__in=filters["licenses"])

        if "min_completeness_score" in filters:
            secondary_query = secondary_query & Q(
                completeness_score__gte=filters["min_completeness_score"]
            )

        if "min_file_size" in filters:
            secondary_query = secondary_query & Q(
                files__file_size_bytes__gte=filters["min_file_size"]["byte_size"]
            )

        if "max_file_size" in filters:
            secondary_query = secondary_query & Q(
                files__file_size_bytes__lte=filters["max_file_size"]["byte_size"]
            )

        if "tags" in filters:
            secondary_query = secondary_query & Q(
                tags__name__in=[tag.lower().strip() for tag in filters["tags"]]
            )

        dataset_query = Dataset.objects.filter(base_query & secondary_query)
        if "sort_keys" in filters:
            dataset_query.order_by(*filters["sort_keys"])

        # Save user search query for trending analysis
        if request.user.is_authenticated and "search" in filters:
            try:
                from trends.models import SearchQuery

                SearchQuery.objects.create(
                    user=request.user, query=filters["search"].strip()
                )
            except Exception:
                pass

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset_query, request)

        response_serializer = DatasetSerializer(instance=page, many=True)
        return paginator.get_paginated_response(response_serializer.data)


class UpdateDatasetView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateDatasetSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self) -> QuerySet[Dataset]:
        owner: User = User.objects.get(id=str(self.request.user.id))
        return Dataset.objects.filter(owner=owner)

    def update(self, request: Request) -> Response:
        if not request.data:
            raise ValidationError(detail={"message": "provide data to update dataset"})
        instance = self.get_object()
        serializer = self.get_serializer(
            instance=instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            data={
                "success": True,
                "message": "successfully updated dataset",
                "dataset": serializer.data,
            }
        )


class RetrieveDatasetView(RetrieveAPIView):
    serializer_class = DatasetSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self) -> QuerySet[Dataset]:
        if self.request.user.is_authenticated:
            return Dataset.objects.filter(
                Q(owner=self.request.user) | Q(is_public=True)
            )
        return Dataset.objects.filter(is_public=True)


class UpdateDatasetVersion(UpdateAPIView):
    serializer_class = UpdateDatasetVersionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self) -> QuerySet[DatasetVersion]:
        owner: User = User.objects.get(id=str(self.request.user.id))
        try:
            dataset = Dataset.objects.get(id=self.kwargs.get("id"), owner=owner)
            return DatasetVersion.objects.filter(owner=owner, dataset=dataset)
        except Dataset.DoesNotExist as e:
            raise ValidationError(
                detail={
                    "message": "dataset does not exist or invalid permission to update"
                }
            ) from e

    def update(self, request: Request, **kwargs: Any) -> Response:
        owner: User = User.objects.get(id=str(request.user.id))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dataset_id: str = kwargs.get("id", "")
        retain_ids = serializer.validated_data.get("dataset_files_to_retain", [])
        current_version_number = serializer.validated_data.get("current_version_number")

        try:
            dataset = Dataset.objects.get(id=dataset_id, owner=owner)
        except Dataset.DoesNotExist as e:
            raise ValidationError(
                {"message": "dataset does not exist or invalid permission to update"}
            ) from e

        try:
            with transaction.atomic():
                try:
                    current_version = DatasetVersion.objects.get(
                        version_number=current_version_number, dataset=dataset
                    )
                    latest_version = (
                        DatasetVersion.objects.filter(dataset=dataset)
                        .order_by("-version_number")
                        .first()
                    )
                    if (
                        latest_version
                        and current_version.version_number
                        != latest_version.version_number
                    ):
                        raise ValidationError(
                            {
                                "message": "can only update the latest version of this dataset"
                            }
                        )
                except DatasetVersion.DoesNotExist as e:
                    raise ValidationError(
                        {"message": "current version does not exist for this dataset"}
                    ) from e

                previous_dataset_files_qs = DatasetFile.objects.filter(
                    dataset_version=current_version
                )
                previous_count = previous_dataset_files_qs.count()

                dataset_files_to_retain_qs = previous_dataset_files_qs.filter(
                    id__in=retain_ids
                )
                retained_file_ids = list(
                    dataset_files_to_retain_qs.values_list("id", flat=True)
                )

                if dataset_files_to_retain_qs.count() != len(retain_ids):
                    raise ValidationError(
                        {
                            "message": "one or more dataset_file ids to retain are missing or invalid"
                        }
                    )

                new_version_number = current_version.version_number + 1
                new_version = DatasetVersion.objects.create(
                    dataset=dataset,
                    version_number=new_version_number,
                    version_label=f"v{new_version_number}",
                    metadata={},
                    changelog=[],
                    owner=owner,
                )

                dataset_files = [
                    DatasetFile(
                        dataset_version=new_version,
                        upload_id=df.upload_id,
                        upload_url=df.upload_url,
                        file_format=df.file_format,
                        file_size_bytes=df.file_size_bytes,
                        checksum=df.checksum,
                        owner=owner,
                        metadata=df.metadata,
                        column_schema=df.column_schema,
                        dataset=dataset,
                    )
                    for df in dataset_files_to_retain_qs
                ]

                new_dataset_files = []
                for uploaded_file in request.FILES.getlist("files", []):
                    # seek before making md5 to make sure the md5 is correct
                    uploaded_file.seek(0)
                    md5_hex = hashlib.md5(uploaded_file.read()).hexdigest()
                    existing_dataset_file = DatasetFile.objects.filter(
                        dataset_version=current_version, checksum=md5_hex
                    ).first()

                    if existing_dataset_file:
                        if existing_dataset_file.id not in retained_file_ids:
                            dataset_files.append(
                                DatasetFile(
                                    dataset_version=new_version,
                                    upload_id=existing_dataset_file.upload_id,
                                    upload_url=existing_dataset_file.upload_url,
                                    file_format=existing_dataset_file.file_format,
                                    file_size_bytes=existing_dataset_file.file_size_bytes,
                                    checksum=existing_dataset_file.checksum,
                                    owner=owner,
                                    metadata=existing_dataset_file.metadata,
                                    column_schema=existing_dataset_file.column_schema,
                                    dataset=dataset,
                                )
                            )
                        continue

                    uploaded_file.seek(0)
                    file_info = upload_datasetfile_to_gcloud(uploaded_file)
                    _, ext = os.path.splitext(uploaded_file.name)
                    ext = ext.lstrip(".")
                    metadata = compute_metadata(uploaded_file) or {}
                    dataset_file = DatasetFile(
                        dataset_version=new_version,
                        upload_id=file_info.id,
                        upload_url=file_info.public_url or "",
                        file_format=ext,
                        file_size_bytes=file_info.size,
                        checksum=md5_hex,
                        owner=owner,
                        metadata={
                            "file_info": metadata.get("file_info"),
                            "structure": metadata.get("structure"),
                            "extraction_timestamp": metadata.get(
                                "extraction_timestamp"
                            ),
                            "failure_reason": metadata.get("failure_reason"),
                            "meta_generation_failure": metadata.get(
                                "meta_generation_failure", False
                            ),
                            "meta_generation_failure_timestamp": metadata.get(
                                "meta_generation_failure_timestamp"
                            ),
                        },
                        column_schema=metadata.get("column_schema", []),
                        dataset=dataset,
                    )

                    new_dataset_files.append(dataset_file)

                # make sure that creating this new version, does not end up the same as old version
                # this means that new_dataset_files is not empty or the length of retained dataset files
                # is not the same as the current version that exists.
                if not new_dataset_files and len(dataset_files) == previous_count:
                    raise ValidationError(
                        {
                            "message": "attempt to create new version causes the same state as previous version"
                        }
                    )

                dataset_files.extend(new_dataset_files)
                DatasetFile.objects.bulk_create(dataset_files)
                new_version.refresh_from_db()

                response_serializer = DatasetVersionSerializer(instance=new_version)
                return Response(data=response_serializer.data, status=201)

        except ValidationError as exc:
            return Response(data=exc.detail, status=400)

        except Exception as exc:
            return Response(
                data={"message": "failed to process version update", "error": str(exc)},
                status=500,
            )


class DeleteDatasetView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def destroy(self, request: Request, **kwargs: Any) -> Response:
        dataset_id: str = kwargs.get("id", "")
        owner: User = User.objects.get(id=str(request.user.id))
        try:
            dataset = Dataset.objects.get(id=dataset_id, owner=owner)
        except Dataset.DoesNotExist as e:
            raise ValidationError(
                {"message": "dataset does not exist or invalid permission to delete"}
            ) from e

        delete_dataset_task(str(dataset.id))

        return Response(
            data={
                "message": f"dataset {dataset.title} deleted",
            },
            status=202,
        )


class DeleteDatasetVersionView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def destroy(self, request: Request, **kwargs: Any) -> Response:
        dataset_version_id: str = kwargs.get("id", "")
        owner: User = User.objects.get(id=str(request.user.id))
        try:
            dataset_version = DatasetVersion.objects.get(
                id=dataset_version_id, owner=owner
            )
        except DatasetVersion.DoesNotExist as e:
            raise ValidationError(
                {
                    "message": "dataset version does not exist or invalid permission to delete"
                }
            ) from e

        delete_version_task(str(dataset_version.id))

        return Response(
            data={
                "message": f"dataset version {dataset_version.version_number} deleted",
            },
            status=202,
        )


class DeleteDatasetFileView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def destroy(self, request: Request, **kwargs: Any) -> Response:
        owner: User = User.objects.get(id=str(request.user.id))
        dataset_file_id: str = kwargs.get("id", "")
        try:
            dataset_file = DatasetFile.objects.get(id=dataset_file_id, owner=owner)
        except DatasetFile.DoesNotExist as e:
            raise ValidationError(
                {
                    "message": "dataset file does not exist or invalid permission to delete"
                }
            ) from e

        delete_file_task(str(dataset_file.id))

        return Response(
            data={
                "message": f"dataset file {dataset_file.upload_id} deleted",
            },
            status=202,
        )
