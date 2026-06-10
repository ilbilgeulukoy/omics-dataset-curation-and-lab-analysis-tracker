from pathlib import Path
import sqlite3
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "omics_tracker.db"


STOPWORDS = {
    "which",
    "what",
    "where",
    "when",
    "why",
    "how",
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "of",
    "for",
    "to",
    "in",
    "on",
    "and",
    "or",
    "with",
    "mention",
    "mentions",
    "datasets",
    "dataset",
}


def clean_query_for_fts(query: str) -> str:
    query = query.strip()
    query = re.sub(r"[^\w\s-]", " ", query)

    terms = [
        term.lower()
        for term in query.split()
        if term and term.lower() not in STOPWORDS
    ]

    if not terms:
        return ""

    return " OR ".join(terms)


def make_preview(text: str, max_chars: int = 420) -> str:
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + "..."


def search_note_chunks(
    query: str,
    max_results: int = 8,
    note_type: str | None = None,
) -> list[dict]:
    if not DB_PATH.exists():
        return []

    fts_query = clean_query_for_fts(query)

    if not fts_query:
        return []

    if note_type:
        sql = """
        SELECT
            c.chunk_id,
            c.file_path,
            c.note_type,
            c.note_name,
            c.section_heading,
            c.content,
            bm25(note_chunks_fts) AS score
        FROM note_chunks_fts
        JOIN note_chunks c ON c.chunk_id = note_chunks_fts.rowid
        WHERE note_chunks_fts MATCH ?
          AND c.note_type = ?
        ORDER BY score
        LIMIT ?
        """

        params = (fts_query, note_type, max_results)

    else:
        sql = """
        SELECT
            c.chunk_id,
            c.file_path,
            c.note_type,
            c.note_name,
            c.section_heading,
            c.content,
            bm25(note_chunks_fts) AS score
        FROM note_chunks_fts
        JOIN note_chunks c ON c.chunk_id = note_chunks_fts.rowid
        WHERE note_chunks_fts MATCH ?
        ORDER BY
            CASE
                WHEN c.note_type = 'dataset' THEN 0
                ELSE 1
            END,
            score
        LIMIT ?
        """

        params = (fts_query, max_results)

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            rows = []

    return [
        {
            "chunk_id": row["chunk_id"],
            "file_path": row["file_path"],
            "note_type": row["note_type"],
            "note_name": row["note_name"],
            "section_heading": row["section_heading"],
            "content": row["content"],
            "preview": make_preview(row["content"]),
            "score": row["score"],
        }
        for row in rows
    ]


def build_grounded_answer(query: str, results: list[dict]) -> str:
    if not results:
        return (
            "No matching curation evidence was found in the indexed Obsidian notes. "
            "Try a more specific query such as H5AD, metadata, preprocessing, synthetic dataset, 10x Genomics, or QC report."
        )

    lines = []
    lines.append("Grounded answer based on indexed Obsidian curation notes:")
    lines.append("")

    top_results = results[:4]

    for index, result in enumerate(top_results, start=1):
        section = result["section_heading"]
        note = result["note_name"]
        preview = result["preview"]

        lines.append(f"{index}. From {note} / {section}:")
        lines.append(f"   {preview}")
        lines.append("")

    lines.append("Sources:")
    for result in top_results:
        lines.append(f"- {result['file_path']} | {result['section_heading']}")

    return "\n".join(lines)


def answer_curation_question(
    query: str,
    max_results: int = 8,
    dataset_first: bool = True,
) -> dict:
    if dataset_first:
        dataset_results = search_note_chunks(
            query=query,
            max_results=max_results,
            note_type="dataset",
        )

        if len(dataset_results) >= max(1, min(3, max_results)):
            results = dataset_results
        else:
            general_results = search_note_chunks(
                query=query,
                max_results=max_results,
                note_type=None,
            )

            seen = set()
            results = []

            for result in dataset_results + general_results:
                key = result["chunk_id"]
                if key in seen:
                    continue
                seen.add(key)
                results.append(result)

            results = results[:max_results]
    else:
        results = search_note_chunks(
            query=query,
            max_results=max_results,
            note_type=None,
        )

    answer = build_grounded_answer(query=query, results=results)

    return {
        "query": query,
        "answer": answer,
        "results": results,
    }


def count_indexed_chunks() -> int:
    if not DB_PATH.exists():
        return 0

    with sqlite3.connect(DB_PATH) as connection:
        try:
            return int(connection.execute("SELECT COUNT(*) FROM note_chunks").fetchone()[0])
        except sqlite3.OperationalError:
            return 0
