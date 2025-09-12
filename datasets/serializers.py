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


class CreateDatasetSerializer(serializers.ModelSerializer):
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
        min_length=1,
    )
    version_label = serializers.CharField(required=False)

    class Meta:
        model = Dataset
        read_only_fields = ["downloads", "views", "completeness_score", "changelog"]
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
