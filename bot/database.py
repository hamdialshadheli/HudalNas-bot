import os
import sqlite3
from datetime import datetime


DB_PATH = os.path.join("data", "huda.db")


def get_connection():
    os.makedirs("data", exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    connection.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        joined_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS menus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        display_order INTEGER DEFAULT 0,
        FOREIGN KEY(parent_id) REFERENCES menus(id)
    );

    CREATE TABLE IF NOT EXISTS contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content_type TEXT NOT NULL,
        text_content TEXT,
        file_id TEXT,
        url TEXT,
        display_order INTEGER DEFAULT 0,
        FOREIGN KEY(menu_id) REFERENCES menus(id)
    );

    CREATE TABLE IF NOT EXISTS media_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        media_type TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(menu_id) REFERENCES menus(id)
    );

    CREATE TABLE IF NOT EXISTS media_group_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        file_id TEXT NOT NULL,
        caption TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(group_id) REFERENCES media_groups(id)
    );
    """)

    connection.commit()
    connection.close()


def register_user(user):
    connection = get_connection()

    connection.execute("""
        INSERT INTO users (
            user_id,
            first_name,
            username,
            joined_at
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username
    """, (
        user.id,
        user.first_name or "",
        user.username or "",
        datetime.utcnow().isoformat()
    ))

    connection.commit()
    connection.close()


def ensure_admin(admin_id):
    connection = get_connection()

    connection.execute(
        "INSERT OR IGNORE INTO admins(user_id) VALUES (?)",
        (admin_id,)
    )

    connection.commit()
    connection.close()


def is_admin(user_id):
    connection = get_connection()

    row = connection.execute(
        "SELECT 1 FROM admins WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    return row is not None


def get_stats():
    connection = get_connection()

    users = connection.execute(
        "SELECT COUNT(*) AS n FROM users"
    ).fetchone()["n"]

    menus = connection.execute(
        "SELECT COUNT(*) AS n FROM menus"
    ).fetchone()["n"]

    contents = connection.execute(
        "SELECT COUNT(*) AS n FROM contents"
    ).fetchone()["n"]

    admins = connection.execute(
        "SELECT COUNT(*) AS n FROM admins"
    ).fetchone()["n"]

    media_groups = connection.execute(
        "SELECT COUNT(*) AS n FROM media_groups"
    ).fetchone()["n"]

    media_items = connection.execute(
        "SELECT COUNT(*) AS n FROM media_group_items"
    ).fetchone()["n"]

    connection.close()

    return users, menus, contents, admins, media_groups, media_items
