"""
Metadata module — manages the SQLite database for tracking ingested sources
and logging user queries.
"""

import sqlite3
import os
from datetime import datetime, timezone


class MetadataDB:
    """Handles all SQLite operations for source tracking and query logging."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the database schema (creates tables if they don't exist)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                url           TEXT NOT NULL UNIQUE,
                scheme_name   TEXT,
                document_type TEXT,
                scraped_date  TEXT NOT NULL,
                chunk_count   INTEGER,
                status        TEXT DEFAULT 'active'
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT NOT NULL,
                user_query    TEXT NOT NULL,
                query_type    TEXT NOT NULL,
                response      TEXT,
                citation_url  TEXT,
                latency_ms    INTEGER
            );
        """)

        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # Source CRUD operations
    # -------------------------------------------------------------------------

    def add_source(self, url: str, scheme_name: str, document_type: str,
                   chunk_count: int, status: str = "active") -> int:
        """Insert or update a source record after ingestion."""
        conn = self._get_connection()
        cursor = conn.cursor()
        scraped_date = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO sources (url, scheme_name, document_type, scraped_date, chunk_count, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                scheme_name = excluded.scheme_name,
                document_type = excluded.document_type,
                scraped_date = excluded.scraped_date,
                chunk_count = excluded.chunk_count,
                status = excluded.status;
        """, (url, scheme_name, document_type, scraped_date, chunk_count, status))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_sources(self) -> list[dict]:
        """Retrieve all source records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources ORDER BY id;")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def update_source_status(self, url: str, status: str):
        """Update the status of a source (e.g., 'active', 'stale', 'failed')."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sources SET status = ? WHERE url = ?;", (status, url))
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # Query log operations
    # -------------------------------------------------------------------------

    def log_query(self, user_query: str, query_type: str, response: str = None,
                  citation_url: str = None, latency_ms: int = None) -> int:
        """Log a user query and its response for analytics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO query_logs (timestamp, user_query, query_type, response, citation_url, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (timestamp, user_query, query_type, response, citation_url, latency_ms))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_recent_logs(self, limit: int = 50) -> list[dict]:
        """Retrieve the most recent query logs."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM query_logs ORDER BY id DESC LIMIT ?;", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
