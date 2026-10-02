import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILES = [
    ROOT
    / "data"
    / "domain_chunks"
    / "finllm_india_clean_chunks.jsonl",

    ROOT
    / "data"
    / "domain_chunks"
    / "indian_financial_news_clean_chunks.jsonl",
]

RAG_DIR = ROOT / "data" / "rag"
DB_FILE = RAG_DIR / "finai_rag.db"


def create_database():

    RAG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    # Main document table.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            document_id TEXT,
            chunk_id TEXT,
            title TEXT,
            company TEXT,
            ticker TEXT,
            exchange TEXT,
            date TEXT,
            url TEXT,
            text TEXT,
            sentiment TEXT,
            summary TEXT
        )
    """)

    # Full-text search index.
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
        USING fts5(
            text,
            content='documents',
            content_rowid='id'
        )
    """)

    connection.commit()

    return connection


def insert_file(connection, path):

    cursor = connection.cursor()

    total = 0

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            cursor.execute(
                """
                INSERT INTO documents (
                    source,
                    document_id,
                    chunk_id,
                    title,
                    company,
                    ticker,
                    exchange,
                    date,
                    url,
                    text,
                    sentiment,
                    summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.get("source", "")),
                    str(record.get("document_id", "")),
                    str(record.get("chunk_id", "")),
                    str(record.get("title", "")),
                    str(record.get("company", "")),
                    str(record.get("ticker", "")),
                    str(record.get("exchange", "")),
                    str(record.get("date", "")),
                    str(record.get("url", "")),
                    str(record.get("text", "")),
                    str(record.get("sentiment", "")),
                    str(record.get("summary", "")),
                )
            )

            total += 1

            if total % 5000 == 0:
                print(
                    f"{path.name}: {total} chunks inserted"
                )

    connection.commit()

    return total


def rebuild_fts(connection):

    cursor = connection.cursor()

    print("\nBuilding full-text search index...")

    cursor.execute(
        """
        INSERT INTO documents_fts(
            rowid,
            text
        )
        SELECT
            id,
            text
        FROM documents
        """
    )

    connection.commit()


def main():

    print("=" * 70)
    print("FINAI RAG INDEX BUILDER")
    print("=" * 70)

    if DB_FILE.exists():

        print("\nExisting RAG database found:")
        print(DB_FILE)

        answer = input(
            "Rebuild it from scratch? [y/N]: "
        ).strip().lower()

        if answer == "y":

            DB_FILE.unlink()

            print("Old database removed.")

        else:

            print(
                "Keeping existing database."
            )
            return

    connection = create_database()

    total = 0

    missing_inputs = []

    for input_file in INPUT_FILES:

        print("\nProcessing:")
        print(input_file)

        if not input_file.exists():
            missing_inputs.append(input_file)
            print(
                "WARNING: File not found:"
            )
            print(input_file)
            continue

        count = insert_file(
            connection,
            input_file
        )

        total += count

        print(
            f"Completed {input_file.name}: "
            f"{count} chunks"
        )

    if total == 0:
        connection.close()

        missing = "\n".join(
            str(path)
            for path in missing_inputs
        )

        raise RuntimeError(
            "No RAG source chunks were indexed. "
            "Provide the required domain chunk files before "
            "building the RAG database."
            + (f"\nMissing inputs:\n{missing}" if missing else "")
        )

    rebuild_fts(connection)

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM documents"
    )

    document_count = cursor.fetchone()[0]

    connection.close()

    print("\n" + "=" * 70)
    print("RAG INDEX COMPLETE")
    print("=" * 70)

    print(
        "Documents/chunks indexed:",
        document_count
    )

    print(
        "Database:",
        DB_FILE
    )

    print("=" * 70)


if __name__ == "__main__":
    main()