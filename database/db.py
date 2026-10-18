import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "spendly.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title       TEXT    NOT NULL,
                amount      REAL    NOT NULL CHECK (amount > 0),
                category    TEXT    NOT NULL DEFAULT 'Other',
                date        TEXT    NOT NULL DEFAULT (date('now')),
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)
    conn.close()


def seed_db():
    conn = get_db()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@example.com", generate_password_hash("password123")),
        )
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@example.com",)
        ).fetchone()
        uid = user["id"]

        sample_expenses = [
            (uid, "Groceries",        45.50,  "Food",          "2026-10-01"),
            (uid, "Netflix",          15.99,  "Entertainment", "2026-10-03"),
            (uid, "Bus pass",         30.00,  "Transport",     "2026-10-05"),
            (uid, "Coffee",            4.20,  "Food",          "2026-10-07"),
            (uid, "Electricity bill", 82.00,  "Utilities",     "2026-10-10"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
            sample_expenses,
        )
    conn.close()
