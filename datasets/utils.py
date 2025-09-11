import os
from datetime import datetime
from typing import Any, TypedDict

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from google.cloud import storage
from google.oauth2 import service_account
from pandas.api.types import infer_dtype, is_numeric_dtype

from core.config import application_config


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

    metadata: dict[str, Any] = {
        "extraction_timestamp": datetime.now().isoformat(),
        "file_info": {
            # TODO: file_encoding
            # TODO: csv_delimiter
            # "csv_delimiter": delimiter,
            "file_size": file.size,
            # "encoding": str(file.)
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
                    float(col_data.mean()) if not pd.isna(
                        col_data.mean()) else None
                )
                median_val = (
                    float(col_data.median()) if not pd.isna(
                        col_data.median()) else None
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
            "unique_element_count": int(col_data.nunique()),
            "mean": mean_val,
            "median": median_val,
            "mode": mode_list,
        }
        column_schema.append(schema)

    metadata["column_schema"] = column_schema
    return metadata
