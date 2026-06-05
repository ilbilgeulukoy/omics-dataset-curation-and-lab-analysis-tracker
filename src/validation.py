import pandas as pd
from src.schema import REQUIRED_COLUMNS, VALID_ASSAY_TYPES


def validate_dataset_schema(df: pd.DataFrame) -> dict:
    """
    Validate the input dataset registry schema.

    Returns a dictionary with:
    - missing_required_columns
    - unknown_assay_types
    - is_valid
    """
    columns = set(df.columns)

    missing_required_columns = [
        col for col in REQUIRED_COLUMNS if col not in columns
    ]

    unknown_assay_types = []
    if "assay_type" in df.columns:
        observed_assays = set(df["assay_type"].dropna().astype(str).unique())
        unknown_assay_types = sorted([
            assay for assay in observed_assays
            if assay not in VALID_ASSAY_TYPES
        ])

    is_valid = (
        len(missing_required_columns) == 0
        and len(unknown_assay_types) == 0
    )

    return {
        "is_valid": is_valid,
        "missing_required_columns": missing_required_columns,
        "unknown_assay_types": unknown_assay_types,
    }


def add_path_availability_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add simple path availability flags based on non-empty path columns.
    This does not check whether files exist on disk yet.
    """
    df = df.copy()

    if "primary_data_path" in df.columns:
        df["primary_data_path_provided"] = df["primary_data_path"].notna() & (
            df["primary_data_path"].astype(str).str.strip() != ""
        )

    if "metadata_path" in df.columns:
        df["metadata_path_provided"] = df["metadata_path"].notna() & (
            df["metadata_path"].astype(str).str.strip() != ""
        )

    if "qc_report_path" in df.columns:
        df["qc_report_path_provided"] = df["qc_report_path"].notna() & (
            df["qc_report_path"].astype(str).str.strip() != ""
        )

    return df
