import itertools
from pathlib import Path

import anndata as ad
import pandas as pd


def load_h5ad_manifest(manifest_path: str) -> pd.DataFrame:
    """
    Load a CSV manifest containing preprocessing-passed h5ad sample paths.

    Required columns:
        dataset_name
        sample_id
        h5ad_path

    Optional:
        dataset_id
    """
    path = Path(manifest_path)

    if not path.exists():
        return pd.DataFrame(columns=["dataset_name", "sample_id", "h5ad_path"])

    df = pd.read_csv(path)

    required = {"dataset_name", "sample_id", "h5ad_path"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "H5AD manifest is missing required columns: "
            + ", ".join(sorted(missing))
        )

    return df


def build_dataset_info_from_h5ad_manifest(
    manifest_path: str,
    registry_df: pd.DataFrame,
) -> dict:
    """
    Build dataset-level info from a sample-level h5ad manifest.

    Dataset-level gene set:
        intersection of genes across all readable sample h5ad files within that dataset.

    Dataset-level cell count:
        sum of n_obs across readable sample h5ad files.

    Patient count:
        taken from registry_df using dataset_name.
    """
    manifest_df = load_h5ad_manifest(manifest_path)

    registry_patients = {}
    if "dataset_name" in registry_df.columns and "n_patients" in registry_df.columns:
        registry_patients = dict(
            zip(
                registry_df["dataset_name"].astype(str),
                pd.to_numeric(registry_df["n_patients"], errors="coerce").fillna(0).astype(int),
            )
        )

    dataset_info = {}

    for _, row in manifest_df.iterrows():
        dataset_name = str(row["dataset_name"])
        sample_id = str(row["sample_id"])
        fp = str(row["h5ad_path"])

        if dataset_name not in dataset_info:
            dataset_info[dataset_name] = {
                "genes": None,
                "n_cells": 0,
                "n_samples": 0,
                "n_patients": registry_patients.get(dataset_name, 0),
                "readable_files": [],
                "missing_or_unreadable_files": [],
            }

        if not Path(fp).exists():
            dataset_info[dataset_name]["missing_or_unreadable_files"].append(fp)
            continue

        try:
            adata = ad.read_h5ad(fp)
        except Exception as exc:
            dataset_info[dataset_name]["missing_or_unreadable_files"].append(
                f"{fp} | READ_ERROR: {exc}"
            )
            continue

        genes = set(adata.var_names.astype(str))

        if dataset_info[dataset_name]["genes"] is None:
            dataset_info[dataset_name]["genes"] = genes
        else:
            dataset_info[dataset_name]["genes"] = dataset_info[dataset_name]["genes"].intersection(genes)

        dataset_info[dataset_name]["n_cells"] += int(adata.n_obs)
        dataset_info[dataset_name]["n_samples"] += 1
        dataset_info[dataset_name]["readable_files"].append(fp)

    for dataset_name in dataset_info:
        if dataset_info[dataset_name]["genes"] is None:
            dataset_info[dataset_name]["genes"] = set()

    return dataset_info


def dataset_info_to_dataframe(dataset_info: dict) -> pd.DataFrame:
    rows = []

    for dataset_name, info in dataset_info.items():
        rows.append({
            "dataset_name": dataset_name,
            "n_patients": info["n_patients"],
            "n_readable_samples": info["n_samples"],
            "n_cells": info["n_cells"],
            "n_genes_after_sample_intersection": len(info["genes"]),
            "n_missing_or_unreadable_files": len(info["missing_or_unreadable_files"]),
        })

    if not rows:
        return pd.DataFrame(
            columns=[
                "dataset_name",
                "n_patients",
                "n_readable_samples",
                "n_cells",
                "n_genes_after_sample_intersection",
                "n_missing_or_unreadable_files",
            ]
        )

    return pd.DataFrame(rows).sort_values("dataset_name").reset_index(drop=True)


def generate_dataset_combinations(
    df: pd.DataFrame,
    h5ad_path_file: str,
    min_common_genes: int = 18000,
    min_total_patients: int = 0,
    min_total_cells: int = 0,
    max_datasets: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate and rank dataset combinations using exact h5ad gene intersections.

    Input:
        sample-level h5ad manifest CSV

    Ranking:
        1. total_patients descending
        2. n_common_genes descending
        3. total_cells descending

    No score.
    No penalty.
    No gene_set_path.
    """
    dataset_info = build_dataset_info_from_h5ad_manifest(
        manifest_path=h5ad_path_file,
        registry_df=df,
    )

    dataset_summary_df = dataset_info_to_dataframe(dataset_info)

    available_datasets = [
        name for name, info in dataset_info.items()
        if len(info["genes"]) > 0 and info["n_samples"] > 0
    ]

    if len(available_datasets) < 2:
        return pd.DataFrame(
            columns=[
                "rank",
                "datasets_in_combo",
                "n_datasets",
                "n_common_genes",
                "total_patients",
                "total_cells",
                "total_samples",
            ]
        ), dataset_summary_df

    if max_datasets is None:
        max_datasets = len(available_datasets)

    max_datasets = min(max_datasets, len(available_datasets))

    rows = []

    for r in range(2, max_datasets + 1):
        for combo in itertools.combinations(available_datasets, r):
            common_genes = set.intersection(*(dataset_info[name]["genes"] for name in combo))
            n_common_genes = len(common_genes)

            total_patients = sum(dataset_info[name]["n_patients"] for name in combo)
            total_cells = sum(dataset_info[name]["n_cells"] for name in combo)
            total_samples = sum(dataset_info[name]["n_samples"] for name in combo)

            if n_common_genes < min_common_genes:
                continue

            if total_patients < min_total_patients:
                continue

            if total_cells < min_total_cells:
                continue

            rows.append({
                "datasets_in_combo": ", ".join(combo),
                "n_datasets": r,
                "n_common_genes": n_common_genes,
                "total_patients": total_patients,
                "total_cells": total_cells,
                "total_samples": total_samples,
            })

    result = pd.DataFrame(rows)

    if result.empty:
        return pd.DataFrame(
            columns=[
                "rank",
                "datasets_in_combo",
                "n_datasets",
                "n_common_genes",
                "total_patients",
                "total_cells",
                "total_samples",
            ]
        ), dataset_summary_df

    result = result.sort_values(
        by=["total_patients", "n_common_genes", "total_cells"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    result.insert(0, "rank", range(1, len(result) + 1))

    return result, dataset_summary_df
