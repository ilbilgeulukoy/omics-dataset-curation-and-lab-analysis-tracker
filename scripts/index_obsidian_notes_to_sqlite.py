from pathlib import Path
import sqlite3
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omics_tracker.db"
OBSIDIAN_VAULT_DIR = PROJECT_ROOT / "obsidian_vault"


def list_markdown_files() -> list[Path]:
    if not OBSIDIAN_VAULT_DIR.exists():
        return []

    markdown_files = sorted(OBSIDIAN_VAULT_DIR.rglob("*.md"))

    # Index only curation content, not vault documentation.
    return [
        path for path in markdown_files
        if path.name.lower() != "readme.md"
    ]


def infer_note_type(path: Path) -> str:
    parts = path.parts

    if "datasets" in parts:
        return "dataset"
    if "protocols" in parts:
        return "protocol"
    if "decisions" in parts:
        return "decision"

    return "general"


def split_markdown_sections(text: str) -> list[dict]:
    lines = text.splitlines()

    sections = []
    current_heading = "Document start"
    current_level = 0
    current_lines = []

    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

    for line in lines:
        match = heading_pattern.match(line)

        if match:
            if current_lines:
                sections.append(
                    {
                        "heading": current_heading,
                        "heading_level": current_level,
                        "content": "\n".join(current_lines).strip(),
                    }
                )

            current_level = len(match.group(1))
            current_heading = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            {
                "heading": current_heading,
                "heading_level": current_level,
                "content": "\n".join(current_lines).strip(),
            }
        )

    return [
        section for section in sections
        if section["heading"].strip() or section["content"].strip()
    ]


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


PLACEHOLDER_PATTERNS = [
    "summarize the main reason why this dataset is useful",
    "describe missing metadata, access restrictions",
    "explain whether this dataset should be included",
    "describe the next concrete review step",
]


def is_placeholder_section(heading: str, content: str) -> bool:
    combined = f"{heading}\n{content}".lower()

    return any(pattern in combined for pattern in PLACEHOLDER_PATTERNS)


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS note_chunks")
    connection.execute("DROP TABLE IF EXISTS note_chunks_fts")

    connection.execute(
        """
        CREATE TABLE note_chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            note_type TEXT NOT NULL,
            note_name TEXT NOT NULL,
            section_heading TEXT NOT NULL,
            heading_level INTEGER,
            content TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE VIRTUAL TABLE note_chunks_fts
        USING fts5(
            file_path,
            note_type,
            note_name,
            section_heading,
            content,
            content='note_chunks',
            content_rowid='chunk_id'
        )
        """
    )


def insert_chunk(
    connection: sqlite3.Connection,
    file_path: str,
    note_type: str,
    note_name: str,
    section_heading: str,
    heading_level: int,
    content: str,
) -> None:
    cursor = connection.execute(
        """
        INSERT INTO note_chunks (
            file_path,
            note_type,
            note_name,
            section_heading,
            heading_level,
            content
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            file_path,
            note_type,
            note_name,
            section_heading,
            heading_level,
            content,
        ),
    )

    chunk_id = cursor.lastrowid

    connection.execute(
        """
        INSERT INTO note_chunks_fts (
            rowid,
            file_path,
            note_type,
            note_name,
            section_heading,
            content
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            chunk_id,
            file_path,
            note_type,
            note_name,
            section_heading,
            content,
        ),
    )


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    markdown_files = list_markdown_files()

    if not markdown_files:
        raise FileNotFoundError(
            f"No markdown notes found inside {OBSIDIAN_VAULT_DIR}. Run export_datasets_to_obsidian.py first."
        )

    total_chunks = 0

    with sqlite3.connect(DB_PATH) as connection:
        create_tables(connection)

        for path in markdown_files:
            relative_path = str(path.relative_to(PROJECT_ROOT))
            note_type = infer_note_type(path)
            note_name = path.stem

            text = path.read_text(encoding="utf-8")
            sections = split_markdown_sections(text)

            for section in sections:
                heading = clean_text(section["heading"])
                content = clean_text(section["content"])

                if not heading and not content:
                    continue

                # Skip empty template sections so retrieval returns real curation evidence.
                if is_placeholder_section(heading, content):
                    continue

                insert_chunk(
                    connection=connection,
                    file_path=relative_path,
                    note_type=note_type,
                    note_name=note_name,
                    section_heading=heading,
                    heading_level=section["heading_level"],
                    content=content,
                )

                total_chunks += 1

        connection.commit()

    print("Obsidian notes indexed into SQLite.")
    print(f"Database path: {DB_PATH}")
    print(f"Markdown files indexed: {len(markdown_files)}")
    print(f"Note chunks indexed: {total_chunks}")


if __name__ == "__main__":
    main()
