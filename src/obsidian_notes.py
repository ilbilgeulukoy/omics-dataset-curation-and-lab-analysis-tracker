from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBSIDIAN_VAULT_DIR = PROJECT_ROOT / "obsidian_vault"
DATASET_NOTES_DIR = OBSIDIAN_VAULT_DIR / "datasets"
PROTOCOLS_DIR = OBSIDIAN_VAULT_DIR / "protocols"
DECISIONS_DIR = OBSIDIAN_VAULT_DIR / "decisions"


def list_dataset_notes() -> list[str]:
    if not DATASET_NOTES_DIR.exists():
        return []

    return sorted([path.name for path in DATASET_NOTES_DIR.glob("*.md")])


def read_dataset_note(filename: str) -> str:
    note_path = DATASET_NOTES_DIR / filename

    if not note_path.exists():
        return "Dataset note not found."

    return note_path.read_text(encoding="utf-8")


def get_note_path(filename: str) -> str:
    return str(DATASET_NOTES_DIR / filename)


def count_dataset_notes() -> int:
    return len(list_dataset_notes())


def list_protocol_notes() -> list[str]:
    if not PROTOCOLS_DIR.exists():
        return []

    return sorted([path.name for path in PROTOCOLS_DIR.glob("*.md")])


def read_protocol_note(filename: str) -> str:
    note_path = PROTOCOLS_DIR / filename

    if not note_path.exists():
        return "Protocol note not found."

    return note_path.read_text(encoding="utf-8")
