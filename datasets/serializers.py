import csv
import json
from io import StringIO
from os import path

import pandas as pd
from django.core.files.base import File
from rest_framework import serializers

from datasets.models import Dataset, DatasetFile, DatasetVersion


class FileExtensionValidator:
    def __init__(self, allowed_extensions: list[str]):
        self.allowed_extensions = allowed_extensions

    def __call__(self, value: File) -> None:
        if not value.name:
            raise serializers.ValidationError("File name cannot be empty")
        _, ext = path.splitext(value.name)
        if ext == ".json":
            try:
                json.loads(value.read())
            except Exception as e:
                raise serializers.ValidationError(
                    "invalid json file was uploaded"
                ) from e

        if ext == ".csv":
            try:
                csv.reader(StringIO(value.read().decode()))
            except Exception as e:
                raise serializers.ValidationError(
                    "invalid csv file was uploaded"
                ) from e

        if ext == ".parquet":
            try:
                pd.read_parquet(value)
            except Exception as e:
                raise serializers.ValidationError(
                    "invalid parquet file was uploaded"
                ) from e

        if ext == ".xlsx":
            try:
                pd.read_excel(value)
            except Exception as e:
                raise serializers.ValidationError(
                    "invalid xlsx file was uploaded"
                ) from e

        if ext not in self.allowed_extensions:
            raise serializers.ValidationError(
                f"invalid file extension. allowed extensions are: {', '.join(self.allowed_extensions)}"
            )


class FileSizeValidator:
    def __init__(self, min_size: int = 0, max_size: int | None = None) -> None:
        self.min_size = min_size
        self.max_size = max_size

    def __call__(self, value: File) -> None:
        if value.size is None:
            raise serializers.ValidationError("File size cannot be determined")

        if value.size < self.min_size:
            raise serializers.ValidationError(
                f"File size {value.size / 1024:.2f} KB is smaller than the minimum {self.min_size / 1024:.2f} KB limit."
            )

        if self.max_size is not None and value.size > self.max_size:
            raise serializers.ValidationError(
                f"File size {value.size / 1024 / 1024:.2f} MB exceeds the {self.max_size / 1024 / 1024:.2f} MB limit."
            )


class CreateDatasetSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=25), required=False
    )
    files = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=False,
            allow_null=False,
            validators=[
                FileExtensionValidator(
                    allowed_extensions=[".csv", ".xlsx", ".json", ".parquet"]
                ),
                FileSizeValidator(max_size=200 * 1024 * 1024),
            ],
        ),
        min_length=1,
    )
    version_label = serializers.CharField(required=False)

    class Meta:
        model = Dataset
        read_only_fields = ["downloads", "views",
                            "completeness_score", "changelog"]
        fields = read_only_fields + [
            "title",
            "description",
            "license",
            "source_org",
            "geography",
            "update_frequency",
            "is_public",
            "metadata",
            "tags",
            "files",
            "version_label",
        ]


class DatasetFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetFile
        # fields = "__all__"
        exclude = ["upload_url"]


class DatasetVersionSerializer(serializers.ModelSerializer):
    files = DatasetFileSerializer(many=True)

    class Meta:
        model = DatasetVersion
        fields = "__all__"


class DatasetSerializer(serializers.ModelSerializer):
    versions = DatasetVersionSerializer(many=True)

    class Meta:
        model = Dataset
        fields = "__all__"


class UpdateDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            "title",
            "description",
            "license",
            "source_org",
            "geography",
            "update_frequency",
            "is_public",
            "metadata",
            "tags"
        ]


class UpdateDatasetVersionSerializer(serializers.Serializer):
    current_version_number = serializers.IntegerField(required=True)
    dataset_files_to_retain = serializers.ListField(
        child=serializers.UUIDField(), default=[], allow_null=False)
    
    files = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=False,
            allow_null=False,
            validators=[
                FileExtensionValidator(
                    allowed_extensions=[".csv", ".xlsx", ".json", ".parquet"]
                )
            ],
        ),
        default=[]
    )
    
    def validate(self, data):
        if not data.get('dataset_files_to_retain') and not data.get('files'):
            raise serializers.ValidationError("Either dataset_files_to_retain or files must be provided")
        return data