from __future__ import annotations
import sqlite3
from typing import List, Optional, Tuple, Dict

DB_FILE = "expenses.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories(
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS expenses(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,        -- ISO 'YYYY-MM-DD'
    amount      REAL NOT NULL,        -- positive
    description TEXT,
    category_id INTEGER,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
);
"""

def connect(db_file: str = DB_FILE) -> sqlite3.Connection:
    con = sqlite3.connect(db_file)
    con.execute("PRAGMA foreign_keys = ON;")
    return con

def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.commit()

# --- Categories ---
def add_category(con: sqlite3.Connection, name: str) -> int:
    cur = con.cursor()
    cur.execute("INSERT INTO categories(name) VALUES(?)", (name.strip(),))
    con.commit()
    return cur.lastrowid

def list_categories(con: sqlite3.Connection) -> List[Tuple[int, str]]:
    cur = con.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name ASC")
    return cur.fetchall()

def get_category_id_by_name(con: sqlite3.Connection, name: str) -> Optional[int]:
    cur = con.cursor()
    cur.execute("SELECT id FROM categories WHERE name = ?", (name.strip(),))
    row = cur.fetchone()
    return row[0] if row else None

# --- Expenses ---
def add_expense(con: sqlite3.Connection, date: str, amount: float, description: str, category_id: Optional[int]) -> int:
    cur = con.cursor()
    cur.execute(
        "INSERT INTO expenses(date, amount, description, category_id) VALUES (?,?,?,?)",
        (date, amount, description.strip() if description else None, category_id),
    )
    con.commit()
    return cur.lastrowid

def list_expenses(con: sqlite3.Connection,
                  date_from: Optional[str] = None,
                  date_to: Optional[str] = None,
                  category_id: Optional[int] = None) -> List[Tuple]:
    q = """
    SELECT e.id, e.date, e.amount, COALESCE(e.description,''),
           COALESCE(c.name, '-')
    FROM expenses e
    LEFT JOIN categories c ON c.id = e.category_id
    WHERE 1=1
    """
    params = []
    if date_from:
        q += " AND e.date >= ?"
        params.append(date_from)
    if date_to:
        q += " AND e.date <= ?"
        params.append(date_to)
    if category_id:
        q += " AND e.category_id = ?"
        params.append(category_id)
    q += " ORDER BY e.date DESC, e.id DESC"
    cur = con.cursor()
    cur.execute(q, params)
    return cur.fetchall()

def delete_expense(con: sqlite3.Connection, expense_id: int) -> bool:
    cur = con.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    con.commit()
    return cur.rowcount > 0

def update_expense(con: sqlite3.Connection, expense_id: int, *, date=None, amount=None, description=None, category_id=None) -> bool:
    fields = []
    params = []
    if date is not None:
        fields.append("date = ?")
        params.append(date)
    if amount is not None:
        fields.append("amount = ?")
        params.append(amount)
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if category_id is not None or category_id is None:
        fields.append("category_id = ?")
        params.append(category_id)
    if not fields:
        return False
    params.append(expense_id)
    q = "UPDATE expenses SET " + ", ".join(fields) + " WHERE id = ?"
    cur = con.cursor()
    cur.execute(q, params)
    con.commit()
    return cur.rowcount > 0

def monthly_totals_by_category(con: sqlite3.Connection, year: int, month: int) -> List[Tuple[str, float]]:
    ym = f"{year:04d}-{month:02d}"
    q = """
    SELECT COALESCE(c.name, '-'), SUM(e.amount) as total
    FROM expenses e
    LEFT JOIN categories c ON c.id = e.category_id
    WHERE e.date LIKE ? || '%'
    GROUP BY c.name
    ORDER BY total DESC
    """
    cur = con.cursor()
    cur.execute(q, (ym,))
    return cur.fetchall()
