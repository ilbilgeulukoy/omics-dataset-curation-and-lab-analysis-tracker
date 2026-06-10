from pathlib import Path
import re
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omics_tracker.db"
VAULT_DIR = PROJECT_ROOT / "obsidian_vault"
DATASET_NOTES_DIR = VAULT_DIR / "datasets"
PROTOCOLS_DIR = VAULT_DIR / "protocols"
DECISIONS_DIR = VAULT_DIR / "decisions"


def safe_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def safe_filename(value: str) -> str:
    value = safe_text(value)
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    value = value.strip("_")
    return value or "unnamed_dataset"


def get_value(row: pd.Series, column: str) -> str:
    if column not in row.index:
        return ""
    return safe_text(row[column])


def make_dataset_note(row: pd.Series) -> str:
    dataset_id = get_value(row, "dataset_id")
    dataset_name = get_value(row, "dataset_name") or dataset_id

    accession = get_value(row, "accession")
    paper_title = get_value(row, "paper_title")
    paper_link = get_value(row, "paper_link")
    data_link = get_value(row, "data_link")
    doi = get_value(row, "doi")
    publication_year = get_value(row, "publication_year")
    first_author = get_value(row, "first_author")

    assay_type = get_value(row, "assay_type")
    disease_area = get_value(row, "disease_area")
    species = get_value(row, "species")
    platform = get_value(row, "platform")
    chemistry_used = get_value(row, "chemistry_used")

    n_patients = get_value(row, "n_patients")
    n_samples = get_value(row, "n_samples")
    n_cells_or_spots = get_value(row, "n_cells_or_spots")
    n_genes = get_value(row, "n_genes")

    data_level = get_value(row, "data_level")
    data_access = get_value(row, "data_access")
    primary_data_path = get_value(row, "primary_data_path")
    metadata_path = get_value(row, "metadata_path")
    qc_report_path = get_value(row, "qc_report_path")

    data_preparation_status = get_value(row, "data_preparation_status")
    data_verification_status = get_value(row, "data_verification_status")
    preprocessing_status = get_value(row, "preprocessing_status")
    verified = get_value(row, "verified")
    include_for_analysis = get_value(row, "include_for_analysis")

    data_verification_comment = get_value(row, "data_verification_comment")
    notes = get_value(row, "notes")

    return f"""# {dataset_name}

## Source

- Dataset ID: {dataset_id}
- Accession: {accession}
- Paper title: {paper_title}
- Paper link: {paper_link}
- Data link: {data_link}
- DOI: {doi}
- Publication year: {publication_year}
- First author: {first_author}

## Dataset metadata

- Assay type: {assay_type}
- Disease area: {disease_area}
- Species: {species}
- Platform: {platform}
- Chemistry used: {chemistry_used}

## Cohort and data size

- Number of patients: {n_patients}
- Number of samples: {n_samples}
- Number of cells or spots: {n_cells_or_spots}
- Number of genes: {n_genes}

## Data availability

- Data level: {data_level}
- Data access: {data_access}
- Primary data path: {primary_data_path}
- Metadata path: {metadata_path}
- QC report path: {qc_report_path}

## Analysis readiness

- Data preparation status: {data_preparation_status}
- Data verification status: {data_verification_status}
- Preprocessing status: {preprocessing_status}
- Verified: {verified}
- Include for analysis: {include_for_analysis}

## Data verification comment

{data_verification_comment}

## Curation notes

{notes}

## Curation interpretation

Summarize the main reason why this dataset is useful, limited, included, or excluded.

## Data limitations

Describe missing metadata, access restrictions, unclear sample mapping, low cohort size, incomplete QC, or other limitations.

## Decision rationale

Explain whether this dataset should be included in downstream analysis or integration, and why.

## Next review action

Describe the next concrete review step for this dataset.

## Links

- Related protocol:
- Related decision note:
- Related datasets:
"""


def write_vault_readme() -> None:
    readme_path = VAULT_DIR / "README.md"
    readme_path.write_text(
        """# Obsidian vault

This folder contains Obsidian-compatible markdown notes generated from the omics dataset curation database.

## Purpose

SQLite stores structured metadata such as dataset identifiers, assay types, verification status, QC paths, and H5AD paths.

Obsidian notes store human-readable curation knowledge such as paper notes, data limitations, manual review comments, and inclusion or exclusion decisions.

## Folder structure

- datasets: one markdown note per dataset
- protocols: reusable curation and verification protocols
- decisions: manual inclusion and exclusion decision notes

## Future RAG layer

These markdown notes can later be indexed by a retrieval-augmented generation system to answer questions such as:

- Why was this dataset excluded?
- Which datasets have incomplete metadata?
- Which datasets are ready for integration?
- Which studies used 10x Genomics?
- What are the main limitations of the included datasets?
""",
        encoding="utf-8",
    )


def write_protocol_note() -> None:
    protocol_path = PROTOCOLS_DIR / "dataset_curation_checklist.md"
    protocol_path.write_text(
        """# Dataset curation review protocol

## Source verification

Review the paper title, DOI, accession, paper link, and data download link.

## Metadata verification

Confirm patient identifiers, sample identifiers, disease area, species, assay type, platform, and chemistry.

## File verification

Confirm the primary data path, metadata path, QC report path, and H5AD path if available.

## Analysis readiness

Evaluate preprocessing status, QC status, metadata completeness, and whether the dataset should be included in downstream analysis.

## Exclusion documentation

If a dataset is excluded, document the reason clearly in the dataset note using the Data limitations and Decision rationale sections.
""",
        encoding="utf-8",
    )


def export_dataset_notes(df: pd.DataFrame) -> int:
    DATASET_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    count = 0

    for _, row in df.iterrows():
        dataset_id = get_value(row, "dataset_id")
        dataset_name = get_value(row, "dataset_name")

        filename_base = dataset_id or dataset_name or f"dataset_{count + 1}"
        filename = safe_filename(filename_base) + ".md"

        note_path = DATASET_NOTES_DIR / filename
        note_path.write_text(make_dataset_note(row), encoding="utf-8")

        count += 1

    return count


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {DB_PATH}. Run scripts/import_csv_to_sqlite.py first."
        )

    VAULT_DIR.mkdir(exist_ok=True)
    DATASET_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    PROTOCOLS_DIR.mkdir(parents=True, exist_ok=True)
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        df = pd.read_sql_query("SELECT * FROM datasets", connection)

    note_count = export_dataset_notes(df)
    write_vault_readme()
    write_protocol_note()

    print("Obsidian export completed.")
    print(f"Vault path: {VAULT_DIR}")
    print(f"Dataset notes exported: {note_count}")


if __name__ == "__main__":
    main()
