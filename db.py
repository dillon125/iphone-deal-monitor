import sqlite3
from contextlib import closing
from pathlib import Path


class SeenListingsDB:
    def __init__(self, db_path: str = "listings.db") -> None:
        self.db_path = Path(db_path)
        self._initialize()

    def _initialize(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_listings (
                    url TEXT PRIMARY KEY,
                    seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def has_seen(self, url: str) -> bool:
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute("SELECT 1 FROM seen_listings WHERE url = ?", (url,)).fetchone()
            return row is not None

    def mark_seen(self, url: str) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("INSERT OR IGNORE INTO seen_listings (url) VALUES (?)", (url,))
            conn.commit()
