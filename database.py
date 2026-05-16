import sqlite3
from datetime import datetime


DB_NAME = "poems.db"


def create_database():
    """Create the poems table if it does not already exist."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            situation TEXT NOT NULL,
            output_language TEXT NOT NULL DEFAULT 'English',
            emotion TEXT NOT NULL,
            style TEXT NOT NULL,
            poetic_influence TEXT NOT NULL DEFAULT 'none',
            title TEXT NOT NULL,
            poem TEXT NOT NULL,
            english_meaning TEXT NOT NULL,
            emotional_theme TEXT NOT NULL,
            alternate_ending TEXT NOT NULL
        )
        """
    )

    cursor.execute("PRAGMA table_info(poems)")
    column_names = [column[1] for column in cursor.fetchall()]
    if "output_language" not in column_names:
        cursor.execute(
            "ALTER TABLE poems ADD COLUMN output_language TEXT NOT NULL DEFAULT 'English'"
        )

    if "poetic_influence" not in column_names:
        cursor.execute(
            "ALTER TABLE poems ADD COLUMN poetic_influence TEXT NOT NULL DEFAULT 'none'"
        )

    connection.commit()
    connection.close()


def save_poem(data):
    """Save one generated poem to SQLite."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO poems (
            created_at,
            situation,
            output_language,
            emotion,
            style,
            poetic_influence,
            title,
            poem,
            english_meaning,
            emotional_theme,
            alternate_ending
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data["situation"],
            data["output_language"],
            data["emotion"],
            data["style"],
            data["poetic_influence"],
            data["title"],
            data["poem"],
            data["english_meaning"],
            data["emotional_theme"],
            data["alternate_ending"],
        ),
    )

    connection.commit()
    connection.close()


def get_poems():
    """Return saved poems from newest to oldest."""
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM poems ORDER BY id DESC")
    poems = cursor.fetchall()

    connection.close()
    return poems


def delete_poem(poem_id):
    """Delete one saved poem."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM poems WHERE id = ?", (poem_id,))

    connection.commit()
    connection.close()


def clear_history():
    """Delete all saved poems."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM poems")

    connection.commit()
    connection.close()
