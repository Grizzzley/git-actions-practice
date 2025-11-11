import pytest
import sqlite3
import os

import db


class MockCursor:
    def execute(self, *args, **kwargs):
        pass


class MockConnection:
    def cursor(self):
        return MockCursor()

    def commit(self):
        raise sqlite3.DatabaseError("commit failed")

    def close(self):
        pass


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    test_db = tmp_path / 'currency_rates.db'
    monkeypatch.setattr(db, 'DB_NAME', str(test_db))
    db.init_db()
    yield
    if os.path.exists(str(test_db)):
        os.remove(str(test_db))


def test_init_db_creates_table():
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='rates'"
    )
    assert cursor.fetchone()[0] == 'rates'
    conn.close()


def test_save_rate_new_record():
    db.save_rate(1, 'USD', 70.55)
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM rates WHERE target_currency='USD'")
    assert cursor.fetchone()[0] == 70.55
    conn.close()


def test_save_rate_update_existing():
    db.save_rate(1, 'USD', 70.55)
    db.save_rate(1, 'USD', 75.11)
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM rates WHERE target_currency='USD'")
    assert cursor.fetchone()[0] == 75.11
    conn.close()


def test_save_rate_date_format():
    db.save_rate(1, 'USD', 70.55)
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT updated_at FROM rates WHERE target_currency='USD'")
    updated_at = cursor.fetchone()[0]
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", updated_at)
    conn.close()


def test_save_rate_multiple_currencies():
    db.save_rate(1, 'USD', 70)
    db.save_rate(2, 'EUR', 80)
    db.save_rate(3, 'GBP', 90)
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM rates")
    assert cursor.fetchone()[0] == 3
    conn.close()


@pytest.mark.parametrize("currency,rate", [
    ("TEST", 0),
    ("NEG", -1.23),
    ("FLOAT", 9999999.99),
    ("LONG", 1e20),
])
def test_save_rate_edge_cases(currency, rate):
    db.save_rate(1, currency, rate)
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rate FROM rates WHERE target_currency=?", (currency,)
    )
    assert cursor.fetchone()[0] == rate
    conn.close()


def test_save_rate_database_connection_error(monkeypatch):
    def bad_connect(*args, **kwargs):
        raise sqlite3.OperationalError("connection failed")
    monkeypatch.setattr(sqlite3, 'connect', bad_connect)
    with pytest.raises(sqlite3.OperationalError):
        db.save_rate(1, 'USD', 65.00)


def test_save_rate_commit_error(monkeypatch):
    monkeypatch.setattr(
        "sqlite3.connect", lambda *args, **kwargs: MockConnection()
    )

    with pytest.raises(sqlite3.DatabaseError):
        db.save_rate(1, 'USD', 65.00)


@pytest.mark.parametrize("id,cur,rate", [
    ("1", "USD", 70.5),
    (None, "EUR", 80),
    (3, 123, 50),
    (4, "USD", "125"),
])
def test_save_rate_parameter_types(id, cur, rate):
    try:
        db.save_rate(id, cur, rate)
    except Exception:
        pass


@pytest.mark.parametrize(
    "currency", ["USD'; DROP TABLE rates; --", "EUR OR 1=1"]
)
def test_save_rate_sql_injection_protection(currency):
    db.save_rate(1, currency, 75)
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rate FROM rates WHERE target_currency=?", (currency,)
    )
    val = cursor.fetchone()
    assert val is not None
    conn.close()


def test_get_saved_rate_success():
    db.save_rate(1, 'USD', 90)
    assert db.get_saved_rate('USD') == 90


def test_get_saved_rate_default_currency():
    db.save_rate(1, 'USD', 70)
    assert db.get_saved_rate('USD') == 70


def test_get_saved_rate_nonexistent_currency():
    assert db.get_saved_rate('ABC') is None


def test_get_saved_rate_empty_database():
    assert db.get_saved_rate('USD') is None


def test_get_saved_rate_multiple_currencies():
    db.save_rate(1, 'USD', 70)
    db.save_rate(2, 'EUR', 80)
    db.save_rate(3, 'GBP', 90)
    assert db.get_saved_rate('USD') == 70
    assert db.get_saved_rate('EUR') == 80
    assert db.get_saved_rate('GBP') == 90


def test_get_saved_rate_case_sensitivity():
    db.save_rate(1, 'usd', 70)
    assert db.get_saved_rate('usd') == 70
    assert db.get_saved_rate('USD') is None


@pytest.mark.parametrize(
    "currency", ["USD'; DROP TABLE rates; --", "EUR OR 1=1"]
)
def test_get_saved_rate_sql_injection_protection(currency):
    db.save_rate(1, currency, 77)
    rate = db.get_saved_rate(currency)
    assert rate == 77


def test_get_saved_rate_database_connection_error(monkeypatch):
    def bad_connect(*args, **kwargs):
        raise sqlite3.OperationalError("fail connect")
    monkeypatch.setattr(sqlite3, 'connect', bad_connect)
    with pytest.raises(sqlite3.OperationalError):
        db.get_saved_rate('USD')
