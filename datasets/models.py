import uuid

from django.db import models


class Dataset(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    title = models.CharField(null=False, max_length=100)
    description = models.TextField(blank=True, default="")
    license = models.CharField(blank=True, max_length=30, default="")
    source_org = models.CharField(blank=True, max_length=30, default="")
    geography = models.CharField(default="Nigeria", max_length=30)
    update_frequency = models.CharField(
        choices=[
            ("monthly", "monthly"),
            ("weekly", "weekly"),
            ("annual", "annual"),
            ("ad_hoc", "ad_hoc"),
            ("never", "never"),
        ],
        blank=True,
        default="never",
    )
    status = models.CharField(
        choices=[
            ("draft", "draft"),
            ("published", "published"),
            ("archived", "archived"),
        ],
        default="draft",
    )
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        "users.User", on_delete=models.DO_NOTHING, related_name="approvals", null=True
    )
    is_public = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    views = models.BigIntegerField(default=0)
    downloads = models.BigIntegerField(default=0)
    owner = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="datasets"
    )
    tags = models.ManyToManyField("datasets.Tag", related_name="datasets", blank=True)
    completeness_score = models.IntegerField(default=1)
    changelog = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class DatasetVersion(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    dataset = models.ForeignKey(
        "datasets.Dataset", on_delete=models.CASCADE, related_name="versions"
    )
    version_label = models.CharField(default="v1.0.0", max_length=20)
    metadata = models.JSONField(default=dict)
    changelog = models.JSONField(default=list)
    owner = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="dataset_versions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("version_label", "dataset")

    def __str__(self) -> str:
        return self.version_label


class DatasetFile(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    dataset_version = models.ForeignKey(
        "datasets.DatasetVersion", on_delete=models.CASCADE, related_name="files"
    )
    upload_id = models.CharField(max_length=100)
    upload_url = models.URLField(blank=True)
    file_format = models.CharField(
        choices=[
            ("csv", "csv"),
            ("xlsx", "xlsx"),
            ("json", "json"),
            ("parquet", "parquet"),
        ]
    )
    file_size_bytes = models.BigIntegerField()
    checksum = models.TextField()
    owner = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="files"
    )
    column_schema = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    downloads = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.upload_id


class Tag(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    name = models.CharField(max_length=25)

    def __str__(self) -> str:
        return self.name
