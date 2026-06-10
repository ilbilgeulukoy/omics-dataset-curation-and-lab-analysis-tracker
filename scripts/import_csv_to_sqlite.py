from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omics_tracker.db"


TABLE_CONFIG = {
    "datasets": {
        "preferred": DATA_DIR / "datasets.csv",
        "fallback": DATA_DIR / "mock_datasets.csv",
    },
    "samples": {
        "preferred": DATA_DIR / "sample_metadata.csv",
        "fallback": None,
    },
    "qc_summary": {
        "preferred": DATA_DIR / "qc_summary.csv",
        "fallback": None,
    },
    "h5ad_files": {
        "preferred": DATA_DIR / "sample_h5ad_paths.csv",
        "fallback": None,
    },
}


def resolve_csv_path(preferred_path: Path, fallback_path: Path | None) -> Path | None:
    if preferred_path.exists():
        return preferred_path

    if fallback_path is not None and fallback_path.exists():
        return fallback_path

    return None


def load_csv_to_table(connection: sqlite3.Connection, table_name: str, csv_path: Path) -> int:
    df = pd.read_csv(csv_path)

    df.columns = [column.strip() for column in df.columns]

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False,
    )

    return len(df)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    imported_tables = []
    skipped_tables = []

    with sqlite3.connect(DB_PATH) as connection:
        for table_name, paths in TABLE_CONFIG.items():
            csv_path = resolve_csv_path(
                preferred_path=paths["preferred"],
                fallback_path=paths["fallback"],
            )

            if csv_path is None:
                skipped_tables.append(table_name)
                continue

            row_count = load_csv_to_table(connection, table_name, csv_path)
            imported_tables.append((table_name, csv_path.name, row_count))

    print("SQLite import completed.")
    print(f"Database path: {DB_PATH}")

    if imported_tables:
        print("\nImported tables:")
        for table_name, csv_name, row_count in imported_tables:
            print(f"- {table_name}: {row_count} rows from {csv_name}")

    if skipped_tables:
        print("\nSkipped tables because CSV files were missing:")
        for table_name in skipped_tables:
            print(f"- {table_name}")


if __name__ == "__main__":
    main()
