from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBSIDIAN_VAULT_DIR = PROJECT_ROOT / "obsidian_vault"


def list_markdown_files() -> list[Path]:
    if not OBSIDIAN_VAULT_DIR.exists():
        return []

    return sorted(OBSIDIAN_VAULT_DIR.rglob("*.md"))


def normalize_text(text: str) -> str:
    return text.lower().strip()


def split_into_sections(markdown_text: str) -> list[dict]:
    lines = markdown_text.splitlines()
    sections = []
    current_title = "Document start"
    current_lines = []

    for line in lines:
        if line.startswith("#"):
            if current_lines:
                sections.append(
                    {
                        "title": current_title,
                        "content": "\n".join(current_lines).strip(),
                    }
                )

            current_title = line.strip("#").strip() or "Untitled section"
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            {
                "title": current_title,
                "content": "\n".join(current_lines).strip(),
            }
        )

    return sections


def make_preview(text: str, query: str, window: int = 220) -> str:
    text_clean = re.sub(r"\s+", " ", text).strip()
    query_clean = normalize_text(query)

    idx = normalize_text(text_clean).find(query_clean)

    if idx == -1:
        return text_clean[:window] + ("..." if len(text_clean) > window else "")

    start = max(0, idx - window // 2)
    end = min(len(text_clean), idx + len(query) + window // 2)

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text_clean) else ""

    return prefix + text_clean[start:end] + suffix


def score_match(text: str, query: str) -> int:
    text_norm = normalize_text(text)
    query_norm = normalize_text(query)

    if not query_norm:
        return 0

    exact_count = text_norm.count(query_norm)

    query_terms = [term for term in re.split(r"\s+", query_norm) if term]
    term_hits = sum(text_norm.count(term) for term in query_terms)

    return exact_count * 5 + term_hits


def search_obsidian_notes(query: str, max_results: int = 20) -> list[dict]:
    query = query.strip()

    if not query:
        return []

    results = []

    for path in list_markdown_files():
        text = path.read_text(encoding="utf-8")
        sections = split_into_sections(text)

        for section in sections:
            section_text = section["title"] + "\n" + section["content"]
            score = score_match(section_text, query)

            if score <= 0:
                continue

            results.append(
                {
                    "score": score,
                    "file": str(path.relative_to(PROJECT_ROOT)),
                    "section": section["title"],
                    "preview": make_preview(section_text, query),
                }
            )

    results = sorted(results, key=lambda item: item["score"], reverse=True)

    return results[:max_results]
