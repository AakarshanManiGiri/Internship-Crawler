import sqlite3
from datetime import datetime

from database.db import Database


TEST_USERS = [
    ("your-email@gmail.com", "{}"),
]


def seed_test_users(db_path: str = "internships.db"):
    database = Database(db_path)

    conn = sqlite3.connect(database.db_path)
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT OR IGNORE INTO users (email, preferences, created_at)
        VALUES (?, ?, ?)
        """,
        [
            (email, preferences, datetime.now().isoformat())
            for email, preferences in TEST_USERS
        ],
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed_test_users()
    print("Test database initialized.")