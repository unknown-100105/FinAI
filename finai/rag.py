import re
import sqlite3
from pathlib import Path


# ============================================================
# FINAI RAG RETRIEVER
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DB_FILE = (
    ROOT
    / "data"
    / "rag"
    / "finai_rag.db"
)


def connect_db():
    """
    Open the FinAI RAG database.
    """

    if not DB_FILE.exists():

        raise FileNotFoundError(
            f"RAG database not found: {DB_FILE}"
        )

    connection = sqlite3.connect(
        DB_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def build_search_query(text: str):
    """
    Convert a natural-language question into
    a safe SQLite FTS5 query.

    We keep meaningful alphanumeric tokens and
    join them with OR so that queries do not
    become unnecessarily strict.
    """

    tokens = re.findall(
        r"[A-Za-z0-9]+",
        text.lower(),
    )

    # Remove very short/common terms.
    tokens = [
        token
        for token in tokens
        if len(token) >= 2
    ]

    # Remove duplicates while preserving order.
    unique_tokens = list(
        dict.fromkeys(tokens)
    )

    if not unique_tokens:
        return None

    # Quote every token for FTS5 safety.
    quoted = [
        f'"{token}"'
        for token in unique_tokens
    ]

    return " OR ".join(quoted)


def search(
    query: str,
    top_k: int = 5,
):
    """
    Retrieve the most relevant financial chunks.
    """

    if not query or not query.strip():

        return []

    fts_query = build_search_query(
        query
    )

    if not fts_query:

        return []

    connection = connect_db()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                d.id,
                d.source,
                d.document_id,
                d.chunk_id,
                d.title,
                d.company,
                d.ticker,
                d.exchange,
                d.date,
                d.url,
                d.text,
                d.sentiment,
                d.summary,
                bm25(documents_fts) AS score
            FROM documents_fts
            JOIN documents AS d
                ON documents_fts.rowid = d.id
            WHERE documents_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (
                fts_query,
                int(top_k),
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def format_context(
    results,
):
    """
    Convert retrieved records into context
    that can later be supplied to FinAI.
    """

    if not results:

        return "No relevant financial documents found."

    sections = []

    for index, result in enumerate(
        results,
        start=1,
    ):

        source = result.get(
            "source",
            "unknown"
        )

        title = result.get(
            "title",
            ""
        )

        company = result.get(
            "company",
            ""
        )

        date = result.get(
            "date",
            ""
        )

        text = result.get(
            "text",
            ""
        )

        header_parts = [
            f"Source {index}",
            f"Dataset: {source}",
        ]

        if title:
            header_parts.append(
                f"Title: {title}"
            )

        if company:
            header_parts.append(
                f"Company: {company}"
            )

        if date:
            header_parts.append(
                f"Date: {date}"
            )

        header = "\n".join(
            header_parts
        )

        sections.append(
            f"{header}\n\n{text}"
        )

    return "\n\n" + (
        "\n\n" + "-" * 70 + "\n\n"
    ).join(sections)


def retrieve_context(
    query: str,
    top_k: int = 5,
):
    """
    One-call helper:
    question -> retrieval -> formatted context
    """

    results = search(
        query=query,
        top_k=top_k,
    )

    context = format_context(
        results
    )

    return results, context