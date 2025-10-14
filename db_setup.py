# db_setup.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/employees.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        base_salary REAL DEFAULT 0,
        join_date TEXT
    );

    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        raw_text TEXT,
        skills TEXT,
        experience_years INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );

    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT,
        candidate_email TEXT,
        scheduled_date TEXT,
        scheduled_time TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        month TEXT,
        days_present INTEGER,
        gross_pay REAL,
        tax REAL,
        net_pay REAL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    );
    """)

      # Optional: insert sample demo data if table empty
    cur.execute("SELECT COUNT(*) FROM employees")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
        INSERT INTO employees (name, email, phone, base_salary, join_date)
        VALUES (?, ?, ?, ?, ?)
        """, [
            ("Ali Khan", "ali12@gmail.com", "+923234567983", 55000.0, "2022-03-15"),
            ("Sara Ahmed", "sara12@gmail.com", "+923234875983", 60000.0, "2021-06-10"),
            ("Zain Malik", "zain12@gmail.com", "+923454507983", 43400.0, "2023-01-20"),
        ])
       # conn.commit()
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Initialized DB at", DB_PATH)
