import csv
import logging
import os
from datetime import datetime, timedelta
from typing import Any, TypedDict
from uuid import UUID

import google.cloud.storage as storage
import pandas as pd
from background_task import background
from charset_normalizer import from_bytes
from django.core.files.uploadedfile import InMemoryUploadedFile
from google.oauth2 import service_account
from pandas.api.types import infer_dtype, is_numeric_dtype

from core.config import application_config
from datasets.models import Dataset, DatasetFile, DatasetVersion

logger = logging.getLogger(__name__)


class FileMetadata(TypedDict):
    extraction_timestamp: str
    file_info: dict[str, str | int]
    structure: dict[str, int | list[str] | tuple[int, int] | str]
    column_schema: list[dict[str, Any]]
    # statistical_summary: dict


def upload_datasetfile_to_gcloud(file: InMemoryUploadedFile) -> storage.Blob:
    cred = service_account.Credentials.from_service_account_info(
        application_config.GOOGLE_SERVICE_ACCOUNT_INFO
    )
    storage_client = storage.Client(credentials=cred)
    bucket = storage_client.bucket(application_config.BUCKET_NAME)

    blob = bucket.blob(file.name)
    blob.upload_from_file(file_obj=file)
    file_info = bucket.get_blob(blob_name=blob.name)
    return file_info


def compute_metadata(file: InMemoryUploadedFile) -> dict[str, Any] | None:
    delimiter = None
    df: pd.DataFrame | None = None
    file.seek(0)
    if not file.name:
        return None
    _, ext = os.path.splitext(file.name)
    if not ext:
        return None

    ext = ext.replace(".", "")

    if ext == "csv":
        df = pd.read_csv(file)

    if ext == "xlsx":
        df = pd.read_excel(file)

    if ext == "json":
        df = pd.read_json(file)

    if ext == "parquet":
        df = pd.read_parquet(file)

    if df is None:
        return None

    try:
        file.seek(0)
        charset_match = from_bytes(file.read())
        file_encoding: str | None = None
        if charset_match:
            best_file_encoding = charset_match.best()
            if best_file_encoding:
                file_encoding = best_file_encoding.encoding

        if ext == "csv":
            file.seek(0)
            sample = file.read(4096)
            dialect = csv.Sniffer().sniff(sample.decode(file_encoding))
            delimiter = dialect.delimiter

        metadata: dict[str, Any] = {
            "extraction_timestamp": datetime.now().isoformat(),
            "file_info": {
                "csv_delimiter": delimiter,
                "file_size": file.size,
                "encoding": file_encoding,
            },
            "structure": {},
            "statistical_summary": {},
        }

        metadata["structure"] = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "shape": df.shape,
        }

        column_schema: list[dict[str, Any]] = []
        for col in df.columns:
            col_data = df[col]
            original_dtype = infer_dtype(col_data)

            # Get top 3 most frequent values
            most_frequent = col_data.value_counts(normalize=True).head(3) * 100
            top3_list = [
                {"value": str(index), "frequency_percent": round(freq, 2)}
                for index, freq in most_frequent.items()
            ]

            # Handle numeric statistics
            mean_val = None
            median_val = None
            if is_numeric_dtype(col_data):
                try:
                    mean_val = (
                        float(col_data.mean()) if not pd.isna(col_data.mean()) else None
                    )
                    median_val = (
                        float(col_data.median())
                        if not pd.isna(col_data.median())
                        else None
                    )
                except Exception:
                    mean_val = None
                    median_val = None

            # Handle mode (convert to serializable format)
            mode_values = col_data.mode()
            mode_list = [
                str(val) for val in mode_values.tolist()[:3]
            ]  # Limit to first 3 modes

            schema: dict[str, Any] = {
                "name": col,
                "type": original_dtype,
                "frequent_occurences": top3_list,
                "missing_or_null_count": int(col_data.isna().sum()),
                "unique_element_count": int(col_data.astype(str).nunique()),
                "mean": mean_val,
                "median": median_val,
                "mode": mode_list,
            }
            column_schema.append(schema)

        metadata["column_schema"] = column_schema
    except Exception as e:
        metadata["failure_reason"] = str(e)
        metadata["meta_generation_failure"] = True
        metadata["meta_generation_failure_timestamp"] = datetime.now().isoformat()
    finally:
        pass

    return metadata


# Completeness score
def compute_completeness(dataset: Dataset) -> int:
    score = 0
    # total = 10

    if dataset.title:
        score += 1

    if dataset.description and len(dataset.description.strip()) >= 20:
        score += 1

    if dataset.license:
        score += 1

    if dataset.source_org:
        score += 1

    if dataset.update_frequency and dataset.update_frequency.lower() != "never":
        score += 1

    if dataset.tags.exists() and dataset.tags.count() >= 3:
        score += 2

    metadata = dataset.metadata or {}
    if metadata and not metadata.get("meta_generation_failure", False):
        score += 2

    column_schema = metadata.get("column_schema", [])
    rows = metadata.get("structure", {}).get("rows", 0)

    if column_schema and rows > 0:
        total_nulls = sum(col.get("missing_or_null_count", 0) for col in column_schema)
        total_cells = rows * len(column_schema)
        null_ratio = total_nulls / total_cells if total_cells > 0 else 1
        if null_ratio < 0.2:
            score += 2

    # return int((score / total) * 100)
    return score


# Dataset deletion from GCS


def delete_blob(blob_name: str) -> bool:
    try:
        cred = service_account.Credentials.from_service_account_info(
            application_config.GOOGLE_SERVICE_ACCOUNT_INFO
        )
        storage_client = storage.Client(credentials=cred)
        bucket = storage_client.bucket(application_config.BUCKET_NAME)

        blob = bucket.blob(blob_name)
        blob.delete()
        return True
    except Exception as e:
        logger.error(f"Failed to delete blob {blob_name}: {e}")
        return False


@background(schedule=0)
def delete_dataset_task(dataset_id: str | UUID) -> None:
    try:
        dataset = Dataset.objects.prefetch_related("files").get(id=dataset_id)
    except Dataset.DoesNotExist:
        logger.warning("Dataset not found")
        return

    for file in dataset.files.all():
        delete_blob(file.upload_id)

    dataset.delete()
    logger.info(f"Dataset {dataset_id} deleted with all versions and files.")


@background(schedule=0)
def delete_version_task(version_id: str | UUID) -> None:
    try:
        version = DatasetVersion.objects.prefetch_related("files").get(id=version_id)
    except DatasetVersion.DoesNotExist:
        logger.warning("Version not found")
        return

    for file in version.files.all():
        delete_blob(file.upload_id)

    version.delete()
    logger.info(f"DatasetVersion {version_id} deleted with all files.")


@background(schedule=0)
def delete_file_task(file_id: str | UUID) -> None:
    try:
        file = DatasetFile.objects.get(id=file_id)
    except DatasetFile.DoesNotExist:
        logger.warning("File not found")
        return

    delete_blob(file.upload_id)
    file.delete()
    logger.info(f"DatasetFile {file_id} deleted.")


def generate_presigned_url(
    blob_id: str,
    expiration: timedelta = timedelta(hours=2),
    raise_exception: bool = True,
) -> str | None:
    try:
        cred = service_account.Credentials.from_service_account_info(
            application_config.GOOGLE_SERVICE_ACCOUNT_INFO
        )
        storage_client = storage.Client(credentials=cred)
        bucket = storage_client.bucket(application_config.BUCKET_NAME)

        blob = bucket.blob(blob_id.removeprefix(f"{bucket.name}/"))
        url: str = blob.generate_signed_url(expiration=expiration)
        return url
    except Exception as e:
        if not raise_exception:
            return None
        raise e
