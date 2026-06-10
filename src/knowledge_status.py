from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omics_tracker.db"
OBSIDIAN_VAULT_DIR = PROJECT_ROOT / "obsidian_vault"
OBSIDIAN_DATASETS_DIR = OBSIDIAN_VAULT_DIR / "datasets"


def database_exists() -> bool:
    return DB_PATH.exists()


def obsidian_vault_exists() -> bool:
    return OBSIDIAN_VAULT_DIR.exists()


def count_obsidian_dataset_notes() -> int:
    if not OBSIDIAN_DATASETS_DIR.exists():
        return 0

    return len(list(OBSIDIAN_DATASETS_DIR.glob("*.md")))


def get_sqlite_table_counts() -> dict:
    if not DB_PATH.exists():
        return {}

    table_counts = {}

    with sqlite3.connect(DB_PATH) as connection:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
            connection,
        )

        for table_name in tables["name"].tolist():
            count_df = pd.read_sql_query(
                f"SELECT COUNT(*) AS n_rows FROM {table_name}",
                connection,
            )
            table_counts[table_name] = int(count_df.loc[0, "n_rows"])

    return table_counts


def get_knowledge_status() -> dict:
    return {
        "database_path": str(DB_PATH),
        "database_exists": database_exists(),
        "obsidian_vault_path": str(OBSIDIAN_VAULT_DIR),
        "obsidian_vault_exists": obsidian_vault_exists(),
        "obsidian_dataset_notes": count_obsidian_dataset_notes(),
        "sqlite_table_counts": get_sqlite_table_counts(),
    }
