import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
configured_database_path = Path(os.environ.get("DATABASE_PATH", "tasks.db"))
DATABASE_PATH = (
    configured_database_path
    if configured_database_path.is_absolute()
    else BASE_DIR / configured_database_path
)


def initialize_db():
    """Initializes the database and creates required tables if they do not exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            parola_hash TEXT NOT NULL
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titlu TEXT NOT NULL,
            descriere TEXT,
            finalizata INTEGER DEFAULT 0,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )
    conn.commit()
    conn.close()


def get_db():
    """Yields a SQLite database connection with foreign key support enabled."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()
