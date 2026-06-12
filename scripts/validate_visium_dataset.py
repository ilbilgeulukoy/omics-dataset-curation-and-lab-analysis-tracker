from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional


MATRIX_DIR_NAME = "filtered_feature_bc_matrix"

REQUIRED_MATRIX_FILES = [
    "matrix.mtx.gz",
    "barcodes.tsv.gz",
    "features.tsv.gz",
]

POSITION_FILES = [
    "tissue_positions.csv",
    "tissue_positions_list.csv",
]

IMAGE_FILES = [
    "tissue_hires_image.png",
    "tissue_lowres_image.png",
]


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def count_spots_from_positions(position_file: Optional[Path]) -> int:
    if position_file is None or not position_file.exists():
        return 0

    try:
        with position_file.open("r", encoding="utf-8") as handle:
            lines = [line for line in handle if line.strip()]
    except UnicodeDecodeError:
        with position_file.open("r", encoding="latin-1") as handle:
            lines = [line for line in handle if line.strip()]

    if not lines:
        return 0

    first_line = lines[0].lower()
    has_header = "barcode" in first_line or "in_tissue" in first_line

    return max(len(lines) - 1, 0) if has_header else len(lines)


def first_existing(paths: List[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists():
            return path
    return None


def infer_readiness_status(
    matrix_files_found: bool,
    spatial_folder_found: bool,
    spatial_archive_found: bool,
    positions_found: bool,
    scalefactors_found: bool,
    image_found: bool,
) -> str:
    if not matrix_files_found:
        return "missing_matrix_files"

    if not spatial_folder_found and spatial_archive_found:
        return "needs_extraction"

    if not spatial_folder_found:
        return "missing_spatial_files"

    if not positions_found:
        return "missing_positions"

    if not scalefactors_found:
        return "missing_scalefactors"

    if not image_found:
        return "missing_image"

    return "ready"


def infer_clustering_suitability(readiness_status: str, n_spots: int, metadata_found: bool) -> str:
    if readiness_status != "ready":
        return "low"

    if n_spots >= 3000 and metadata_found:
        return "high"

    if n_spots > 0:
        return "medium"

    return "low"


def validate_sample(
    dataset_id: str,
    sample_id: str,
    sample_path: Path,
    metadata_path: Optional[Path] = None,
) -> Dict[str, object]:
    matrix_dir = sample_path / MATRIX_DIR_NAME
    spatial_dir = sample_path / "spatial"
    spatial_zip = sample_path / "spatial.zip"

    matrix_files_found = matrix_dir.exists() and all((matrix_dir / filename).exists() for filename in REQUIRED_MATRIX_FILES)

    spatial_folder_found = spatial_dir.exists() and spatial_dir.is_dir()
    spatial_archive_found = spatial_zip.exists()

    position_file = first_existing([spatial_dir / filename for filename in POSITION_FILES])
    positions_found = position_file is not None

    scalefactors_file = spatial_dir / "scalefactors_json.json"
    scalefactors_found = scalefactors_file.exists()

    image_file = first_existing([spatial_dir / filename for filename in IMAGE_FILES])
    image_found = image_file is not None

    metadata_found = metadata_path.exists() if metadata_path else False
    n_spots = count_spots_from_positions(position_file)

    readiness_status = infer_readiness_status(
        matrix_files_found=matrix_files_found,
        spatial_folder_found=spatial_folder_found,
        spatial_archive_found=spatial_archive_found,
        positions_found=positions_found,
        scalefactors_found=scalefactors_found,
        image_found=image_found,
    )

    clustering_suitability = infer_clustering_suitability(
        readiness_status=readiness_status,
        n_spots=n_spots,
        metadata_found=metadata_found,
    )

    missing_items = []

    if not matrix_files_found:
        missing_items.append("matrix files")

    if not spatial_folder_found and not spatial_archive_found:
        missing_items.append("spatial folder")

    if not positions_found:
        missing_items.append("positions file")

    if not scalefactors_found:
        missing_items.append("scalefactors file")

    if not image_found:
        missing_items.append("histology image")

    if not metadata_found:
        missing_items.append("metadata")

    if spatial_archive_found and not spatial_folder_found:
        notes = "spatial.zip found but spatial folder not extracted"
    elif missing_items:
        notes = "Missing: " + ", ".join(missing_items)
    else:
        notes = "Complete Visium-like sample structure"

    return {
        "dataset_id": dataset_id,
        "sample_id": sample_id,
        "technology": "Spatial / Visium",
        "sample_path": str(sample_path),
        "matrix_files_found": yes_no(matrix_files_found),
        "spatial_folder_found": yes_no(spatial_folder_found),
        "spatial_archive_found": yes_no(spatial_archive_found),
        "image_found": yes_no(image_found),
        "positions_found": yes_no(positions_found),
        "scalefactors_found": yes_no(scalefactors_found),
        "metadata_found": yes_no(metadata_found),
        "n_spots": n_spots,
        "readiness_status": readiness_status,
        "clustering_suitability": clustering_suitability,
        "notes": notes,
    }


def read_registry(registry_csv: Path) -> List[Dict[str, str]]:
    with registry_csv.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    required_columns = {"dataset_id", "sample_id", "sample_path"}
    missing_columns = required_columns.difference(reader.fieldnames or [])

    if missing_columns:
        raise ValueError(
            "Registry CSV is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    return rows


def write_report(rows: List[Dict[str, object]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "dataset_id",
        "sample_id",
        "technology",
        "sample_path",
        "matrix_files_found",
        "spatial_folder_found",
        "spatial_archive_found",
        "image_found",
        "positions_found",
        "scalefactors_found",
        "metadata_found",
        "n_spots",
        "readiness_status",
        "clustering_suitability",
        "notes",
    ]

    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate 10x Visium-like sample folder structure and write a spatial readiness report."
    )

    parser.add_argument(
        "--sample-dir",
        type=Path,
        help="Path to one Visium sample folder.",
    )

    parser.add_argument(
        "--dataset-id",
        default="DEMO_SPATIAL_DATASET",
        help="Dataset identifier used with --sample-dir.",
    )

    parser.add_argument(
        "--sample-id",
        default="DEMO_SPATIAL_SAMPLE",
        help="Sample identifier used with --sample-dir.",
    )

    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=None,
        help="Optional metadata file path used with --sample-dir.",
    )

    parser.add_argument(
        "--registry-csv",
        type=Path,
        help="CSV with dataset_id, sample_id, sample_path and optional metadata_path columns.",
    )

    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("reports/spatial_readiness_summary.csv"),
        help="Output CSV report path.",
    )

    args = parser.parse_args()

    results: List[Dict[str, object]] = []

    if args.registry_csv:
        rows = read_registry(args.registry_csv)
        for row in rows:
            metadata_value = row.get("metadata_path", "").strip()
            metadata_path = Path(metadata_value) if metadata_value else None

            results.append(
                validate_sample(
                    dataset_id=row["dataset_id"],
                    sample_id=row["sample_id"],
                    sample_path=Path(row["sample_path"]),
                    metadata_path=metadata_path,
                )
            )

    elif args.sample_dir:
        results.append(
            validate_sample(
                dataset_id=args.dataset_id,
                sample_id=args.sample_id,
                sample_path=args.sample_dir,
                metadata_path=args.metadata_path,
            )
        )

    else:
        raise SystemExit("Provide either --sample-dir or --registry-csv.")

    write_report(results, args.output_csv)

    print(f"Wrote spatial readiness report: {args.output_csv}")
    print(f"Validated samples: {len(results)}")


if __name__ == "__main__":
    main()
