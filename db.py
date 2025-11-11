import sqlite3

DB_NAME = 'currency_rates.db'


def init_db() -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_currency TEXT UNIQUE,
        rate REAL,
        updated_at TEXT
    )
    ''')
    conn.commit()
    conn.close()


def save_rate(id: int, target_currency: str, rate: float) -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rates (id, target_currency, rate, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(target_currency) DO UPDATE SET
        rate = excluded.rate,
        updated_at = CURRENT_TIMESTAMP
    ''', (id, target_currency, rate))
    conn.commit()
    conn.close()


def get_saved_rate(target_currency: str) -> float:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT rate FROM rates WHERE target_currency = ?', (target_currency,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
